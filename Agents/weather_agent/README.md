# AI Weather Agent

An end-to-end AI agent that accepts a natural-language weather question, extracts the city, calls a custom weather tool, retrieves real-time data from Open-Meteo, and produces a grounded response.

This project uses:

- OpenAI for natural-language understanding and tool selection
- LangChain for agent and tool orchestration
- LangGraph as the agent execution runtime
- LangSmith for tracing and observability
- Open-Meteo for geocoding and current weather data

## Example

**User prompt**

```text
What is the current weather in Milpitas?
```

**Agent behavior**

```text
User prompt
    ↓
AI identifies a current-weather request
    ↓
AI extracts city = "Milpitas"
    ↓
AI selects get_weather_for_city
    ↓
Tool calls Open-Meteo *geocoding* API
    ↓
"Milpitas" becomes latitude + longitude + timezone
    ↓
Tool calls Open-Meteo *forecast* API
    ↓
Structured weather data is returned
    ↓
AI generates a grounded answer
```

Example response:

```text
The current weather in Milpitas, California, is clear with a
temperature of 73.1°F. It feels like 72.4°F, with 52% humidity
and winds around 11.2 mph.
```

## Repository Setup

Clone the GitHub project:

```bash
git clone https://github.com/shrads22-git/langgraph-learning.git
cd langgraph-learning
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify that the virtual environment is active:

```bash
which python
python --version
```

The Python path should point to:

```text
langgraph-learning/.venv/bin/python
```

## Install Dependencies

Install the required packages:

```bash
python -m pip install --upgrade pip
python -m pip install \
  langchain \
  langgraph \
  langchain-openai \
  langsmith \
  python-dotenv \
  requests
```

Verify the installation:

```bash
python -c "import langchain, langgraph, langchain_openai, langsmith, dotenv, requests; print('Dependencies installed')"
```

## Environment Variables

Create a `.env` file at the root of `langgraph-learning`:

```text
langgraph-learning/.env
```

Add:

```env
OPENAI_API_KEY=your-openai-api-key
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=weather-agent
OPENAI_MODEL=gpt-5.6-luna
```

The `.env` file contains secrets and must never be committed to GitHub.

### `.gitignore`

The root `.gitignore` contains:

```gitignore
.venv/
.env
__pycache__/
*.py[cod]
.pytest_cache/
.DS_Store
```

An `.env.example` file can be committed safely:

```env
OPENAI_API_KEY=your-openai-api-key
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=weather-agent
OPENAI_MODEL=gpt-5.6-luna
```

## Project Structure

```text
langgraph-learning/
├── .env
├── .gitignore
├── .venv/
└── Agents/
    └── weather_agent/
        ├── agent.py
        ├── weather_tool.py
        ├── weather_codes.py
        ├── README.md
        ├── evals/
        └── tests/
```

## Components

### `weather_codes.py`

Open-Meteo returns weather conditions using numeric WMO codes.

Examples:

```text
0  → Clear sky
61 → Slight rain
95 → Thunderstorm
```

`describe_weather_code()` converts the numeric code into a readable description.

```python
describe_weather_code(61)
```

returns:

```text
Slight rain
```

Run its direct test with:

```bash
python weather_codes.py
```

The `if __name__ == "__main__":` block ensures that the test runs only when the file is executed directly, not when another file imports it.

### `weather_tool.py`

This file contains the deterministic weather functions.

#### `get_coordinates(city)`

Converts a city name into:

- Canonical city name
- State or region
- Country
- Latitude
- Longitude
- Timezone

Example:

```python
get_coordinates("Milpitas")
```

The function calls the Open-Meteo geocoding API:

```text
https://geocoding-api.open-meteo.com/v1/search
```

#### `get_current_weather(latitude, longitude, timezone)`

Uses the coordinates to retrieve:

- Current conditions
- Temperature
- Feels-like temperature
- Humidity
- Precipitation
- Wind speed
- Local observation time

The function calls:

```text
https://api.open-meteo.com/v1/forecast
```

#### `get_weather(city)`

Combines the location and weather operations:

```text
get_coordinates(city)
        ↓
get_current_weather(latitude, longitude, timezone)
        ↓
combined result
```

Example:

```python
get_weather("Milpitas")
```

The tool returns structured data instead of a prewritten sentence:

```python
{
    "city": "Milpitas",
    "state": "California",
    "country": "United States",
    "latitude": 37.42827,
    "longitude": -121.90662,
    "timezone": "America/Los_Angeles",
    "condition": "Clear sky",
    "temperature_f": 73.1,
    "feels_like_f": 72.4,
    "humidity_percent": 52,
    "precipitation_inches": 0.0,
    "wind_speed_mph": 11.2,
}
```

Run the deterministic tool:

```bash
python weather_tool.py
```

The terminal asks for a city:

```text
Enter a city:
```

### Error Handling

The tool uses `raise` to signal invalid states:

```python
raise ValueError("City name cannot be empty.")
```

The command-line layer catches expected errors with `try/except` and displays a clean message instead of a traceback.

Handled cases include:

- Blank city
- Unknown location
- HTTP request failure
- Missing current-weather data

## AI Agent

### `agent.py`

`agent.py` exposes the deterministic weather function as a LangChain tool:

```python
@tool
def get_weather_for_city(city: str) -> dict:
    """Get the current weather for a city."""
    return get_weather(city)
```

The `@tool` decorator gives the model:

- A tool name
- A tool description
- An input schema
- An output contract

The agent is created with:

```python
weather_agent = create_agent(
    model=model,
    tools=[get_weather_for_city],
    system_prompt=...,
)
```

The model decides whether the prompt requires the weather tool and extracts the city argument.

Run the agent:

```bash
python agent.py
```

Enter:

```text
What is the current weather in Milpitas?
```

## Agent Scope

The current version supports current weather only.

Supported:

```text
What is the current weather in Milpitas?
How windy is it in Seattle right now?
What is the temperature in New York?
```

Not currently supported:

```text
How will the weather be in December 2026?
What was the weather last month?
Will it rain next week?
```

For unsupported future or historical requests, the agent should explain the limitation instead of inventing or estimating weather.

## LangSmith Observability

When these variables are configured:

```env
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=weather-agent
```

each agent execution is recorded in LangSmith.

A successful trace shows:

1. User prompt
2. Model decision
3. Tool selection
4. Extracted city argument
5. Weather-tool execution
6. Tool result
7. Final model response
8. Token usage and latency

The expected successful trajectory is:

```text
User
→ Model
→ get_weather_for_city
→ Open-Meteo
→ Model
→ Final answer
```

LangSmith allows inspection of whether the agent:

- Selected the correct tool
- Passed the correct city
- Used the tool result
- Avoided unsupported claims
- Produced unnecessary tool calls
- Encountered latency or execution errors

## Why This Is an AI Agent

This is more than a normal API script because the model decides:

- Whether a tool is needed
- Which tool to use
- What arguments to pass
- How to interpret the result
- How to communicate the answer

The weather API call itself is deterministic. The model’s tool selection and final answer are non-deterministic and therefore require agent evaluation.

## Current Status

Completed:

- [x] GitHub project structure
- [x] Python virtual environment
- [x] Secure API-key configuration
- [x] LangSmith tracing configuration
- [x] WMO weather-code mapping
- [x] City geocoding
- [x] Current-weather retrieval
- [x] Combined `get_weather(city)` function
- [x] Input and API error handling
- [x] LangChain tool creation
- [x] OpenAI agent integration
- [x] Natural-language prompt execution
- [x] LangSmith agent traces

Next:

- [ ] Create the weather-agent golden dataset
- [ ] Add deterministic tool unit tests
- [ ] Evaluate tool-selection accuracy
- [ ] Evaluate city-argument accuracy
- [ ] Evaluate unsupported tool-call rate
- [ ] Evaluate response grounding
- [ ] Add trajectory regression tests
- [ ] Add CI evaluation gates
- [ ] Explore Promptfoo evaluation

## Planned Evaluation Thresholds

| Metric | Threshold | Gate |
|---|---:|---|
| Tool Selection Accuracy | 100% | Hard |
| City Argument Accuracy | 100% | Hard |
| Unsupported Tool Call Rate | 0% | Hard |
| Unhandled Error Rate | 0% | Hard |
| Response Grounding | 100% | Hard |

Because weather changes continuously, the evaluation will not compare the response with one fixed temperature. Instead, it will verify properties such as:

- The correct tool was selected
- The correct city was passed
- Weather values came from the tool result
- Unsupported future forecasts were not invented
- Missing locations triggered clarification
- Invalid locations were handled safely

## Technologies

- Python
- OpenAI
- LangChain
- LangGraph
- LangSmith
- Open-Meteo
- Requests
- Git and GitHub
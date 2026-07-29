# AI Weather Agent

An end-to-end AI agent that accepts natural-language weather questions, determines whether a weather tool is required, extracts the city, retrieves current conditions from Open-Meteo, and produces a grounded response.

The project also includes a deterministic evaluation framework for testing agent behavior, tool-call trajectories, grounding, reliability, error handling, and latency.

## Technologies

- Python
- OpenAI
- LangChain
- LangGraph
- LangSmith
- Open-Meteo
- Requests
- Pytest
- Git and GitHub

## System Overview

The project uses:

- **OpenAI** for natural-language understanding, tool selection, and response generation
- **LangChain** for agent and tool orchestration
- **LangGraph** as the agent execution runtime
- **LangSmith** for tracing and observability
- **Open-Meteo** for geocoding and current weather data
- **Pytest** for unit testing
- **Custom code-based evaluators** for agent evaluation

## Example

### User prompt

```text
What is the current weather in Milpitas?
```

### Expected trajectory

```text
User prompt
    ↓
Model identifies a current-weather request
    ↓
Model extracts city = "Milpitas"
    ↓
Model selects get_weather_for_city
    ↓
Tool calls the Open-Meteo geocoding API
    ↓
City becomes latitude + longitude + timezone
    ↓
Tool calls the Open-Meteo forecast API
    ↓
Structured weather data is returned
    ↓
Model produces a grounded answer
```

Example response:

```text
Current weather in Milpitas, California:

- Condition: Clear sky
- Temperature: 62°F
- Feels like: 62.7°F
- Humidity: 86%
- Precipitation: 0 inches
- Wind: 4.5 mph
```

Weather values change continuously, so the exact response will vary between runs.

## Agent Scope

The current version supports current weather for a specific city.

### Supported requests

- Current temperature
- Current weather condition
- Feels-like temperature
- Humidity
- Precipitation
- Wind speed
- Current weather for a specific city

Examples:

```text
What is the current weather in Milpitas?
How windy is it in Seattle right now?
Is it raining in New York City?
```

### Unsupported requests

- Future forecasts
- Historical weather
- Flight status or cancellation predictions
- Tides and marine conditions
- Astronomy and meteor showers
- Future travel recommendations
- Country-level or overly broad locations without a city

Examples:

```text
How will the weather be in December 2026?
Will flights get canceled in Los Angeles due to weather?
When is the next meteor shower in Chicago?
Is it high tide in Miami right now?
What is the weather like in India?
```

For unsupported requests, the agent should explain its limitation without inventing, estimating, or predicting unavailable information.

## Repository Setup

Clone the repository:

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
  requests \
  pytest
```

Alternatively, install from the project requirements file:

```bash
python -m pip install -r requirements.txt
```

Verify the installation:

```bash
python -c "import langchain, langgraph, langchain_openai, langsmith, dotenv, requests, pytest; print('Dependencies installed')"
```

## Environment Variables

Create a `.env` file at the root of `langgraph-learning`:

```text
langgraph-learning/.env
```

Add:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=your-supported-model

LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langgraph-learning
```

The `.env` file contains secrets and must never be committed to GitHub.

An `.env.example` file may be committed safely:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=your-supported-model

LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langgraph-learning
```

### `.gitignore`

The root `.gitignore` should contain:

```gitignore
.venv/
.env
__pycache__/
*.py[cod]
.pytest_cache/
.DS_Store
```

## Project Structure

```text
langgraph-learning/
├── .env.example
├── .gitignore
├── README.md
├── main.py
├── requirements.txt
└── Agents/
    └── weather_agent/
        ├── agent.py
        ├── weather_codes.py
        ├── weather_tool.py
        ├── README.md
        ├── evals/
        │   ├── evaluators.py
        │   ├── eval-spec.md
        │   ├── run_evals.py
        │   ├── run_reliability.py
        │   ├── weather-agent-golden-v1.csv
        │   └── results/
        │       ├── latest-results.csv
        │       ├── reliability-details.csv
        │       └── reliability-summary.csv
        └── tests/
            ├── test_agent.py
            ├── test_evaluators.py
            ├── test_weather_codes.py
            └── test_weather_tool.py
```

## Components

### `weather_codes.py`

Open-Meteo returns weather conditions using numeric WMO weather codes.

Examples:

```text
0  → Clear sky
61 → Slight rain
95 → Thunderstorm
```

The function:

```python
describe_weather_code(code)
```

converts a WMO code into a readable description.

For example:

```python
describe_weather_code(61)
```

returns:

```text
Slight rain
```

Unknown codes are handled explicitly:

```python
describe_weather_code(999)
```

returns:

```text
Unknown weather code (999)
```

A missing code returns:

```text
Unknown
```

Run the file directly:

```bash
python weather_codes.py
```

The following guard ensures that example code executes only when the file is run directly:

```python
if __name__ == "__main__":
```

It does not execute when another module imports `weather_codes.py`.

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

Uses coordinates and timezone information to retrieve:

- Current condition
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

The API is configured to return:

- Temperature in Fahrenheit
- Wind speed in miles per hour
- Precipitation in inches

#### `get_weather(city)`

Combines location lookup and weather retrieval:

```text
get_coordinates(city)
        ↓
get_current_weather(latitude, longitude, timezone)
        ↓
combined location and weather result
```

Example:

```python
get_weather("Milpitas")
```

The function returns structured data:

```python
{
    "city": "Milpitas",
    "state": "California",
    "country": "United States",
    "latitude": 37.42827,
    "longitude": -121.90662,
    "timezone": "America/Los_Angeles",
    "time": "2026-07-28T21:45",
    "condition": "Clear sky",
    "temperature_f": 62.0,
    "feels_like_f": 62.7,
    "humidity_percent": 86,
    "precipitation_inches": 0.0,
    "wind_speed_mph": 4.5,
}
```

Run the deterministic tool directly:

```bash
cd Agents/weather_agent
python weather_tool.py
```

The terminal asks for a city:

```text
Enter a city:
```

## Error Handling

The deterministic weather layer raises exceptions for invalid states.

Examples:

```python
raise ValueError("City name cannot be empty.")
```

```python
raise ValueError(
    f"Could not find a location named '{city}'."
)
```

Handled failure conditions include:

- Blank city input
- Unknown location
- HTTP request failure
- Missing geocoding results
- Missing current-weather data

### Structured tool results

The agent-facing tool converts expected location errors into structured results.

A successful tool result follows this contract:

```python
{
    "status": "success",
    "data": {
        "city": "Milpitas",
        "condition": "Clear sky",
        "temperature_f": 62.0,
    },
}
```

An invalid location follows this contract:

```python
{
    "status": "error",
    "error_type": "location_not_found",
    "message": "Could not find a location named 'NotARealCity12345'.",
}
```

This distinction prevents expected user-input errors from escaping as unhandled agent exceptions.

It also separates two evaluation concepts:

- **Tool execution status:** Did LangGraph successfully execute the tool?
- **Domain status:** Did the weather operation itself succeed or return an expected application error?

For an invalid city, tool execution can be successful while domain status is `error`.

## AI Agent

### `agent.py`

`agent.py` exposes the deterministic weather function as a LangChain tool:

```python
@tool
def get_weather_for_city(city: str) -> dict:
    """Get the current weather for a city."""
```

The `@tool` decorator provides the model with:

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

The model determines:

- Whether the weather tool is necessary
- Whether the request is within scope
- Which city should be passed to the tool
- How to present the tool result
- When clarification is required
- When an unsupported request should be declined

Run the agent:

```bash
cd Agents/weather_agent
python agent.py
```

Example input:

```text
What is the current weather in Milpitas?
```

## Why This Is an AI Agent

This project is more than a standard weather API script because the model makes decisions.

The model determines:

- Whether a tool is needed
- Which tool to use
- What arguments to pass
- Whether a request is supported
- How to interpret structured results
- How to communicate the final answer

The Open-Meteo functions are primarily deterministic. The model’s tool selection, argument extraction, and final response are non-deterministic.

Because of that non-determinism, the agent requires both conventional unit tests and agent-specific evaluations.

# Testing and Evaluation

The project uses multiple testing layers.

```text
Unit tests
    ↓
Deterministic code-based agent evaluations
    ↓
Repeated-run reliability evaluation
    ↓
LangSmith trace inspection
    ↓
LLM-as-a-Judge evaluation (next phase)
```

Each layer evaluates a different type of risk.

## Unit Tests

Unit tests validate individual Python functions in isolation.

### `test_weather_codes.py`

Tests:

- Known WMO weather codes
- Missing weather codes
- Unknown weather codes

### `test_weather_tool.py`

Tests:

- Empty city validation
- Successful coordinate lookup
- Unknown-location handling
- HTTP error propagation
- Current-weather normalization
- Missing weather data
- Combined location and weather output

Network dependencies are mocked so the tests remain:

- Fast
- Deterministic
- Repeatable
- Independent of Open-Meteo availability

### `test_agent.py`

Tests:

- Tool metadata
- Tool input schema
- City argument forwarding
- Successful structured tool output
- Structured invalid-location output
- Unexpected service-error behavior

### `test_evaluators.py`

Tests every deterministic evaluator using controlled pass and fail examples.

This is important because an incorrect evaluator can produce misleading agent-quality results.

Run all unit tests:

```bash
cd Agents/weather_agent
python -m pytest tests -v
```

Run one test file:

```bash
python -m pytest tests/test_weather_tool.py -v
```

Run only grounding-related evaluator tests:

```bash
python -m pytest tests/test_evaluators.py \
  -k "response_fields or extract_numbers or numeric_grounding or condition_grounding" \
  -v
```

## Golden Evaluation Dataset

The golden dataset is stored at:

```text
evals/weather-agent-golden-v1.csv
```

Each row defines:

- Case ID
- User prompt
- Whether a tool should be called
- Expected city argument
- Expected agent behavior
- Expected grounded response fields
- Risk being evaluated

Schema:

```csv
case_id,user_prompt,expected_tool_called,expected_city,expected_behavior,expected_response_fields,risk
```

Example:

```csv
W001,What is the current weather in Milpitas?,yes,Milpitas,weather_answer,condition|temperature_f,Baseline tool selection
```

The dataset covers:

- Supported current-weather requests
- Correct city extraction
- Future requests
- Out-of-scope questions
- Invalid locations
- Country-level locations
- Flight-cancellation questions
- Astronomy requests
- Tide requests
- Future travel recommendations

Blank `expected_city` values are intentional for cases where no tool should be called.

For example, a prompt may mention Los Angeles, but if the request asks the agent to predict flight cancellations, the expected behavior is to avoid the weather tool.

## Evaluation Specification

The evaluation contract is documented in:

```text
evals/eval-spec.md
```

It defines:

- Product capability
- Supported and unsupported requests
- Evaluation dimensions
- Expected trajectories
- Severity levels
- Thresholds
- Pass and failure criteria

The specification is separate from the evaluator implementation so expected behavior can be reviewed before inspecting test results.

## Deterministic Code-Based Evaluators

The evaluator functions are implemented in:

```text
evals/evaluators.py
```

The deterministic evaluation layer checks:

| Evaluator | Purpose |
|---|---|
| Tool called | Verifies whether any tool was called when expected |
| Tool name | Verifies that `get_weather_for_city` was selected |
| Tool-call count | Requires exactly one call for supported requests and zero otherwise |
| City argument | Compares the extracted city with the golden expectation |
| Tool execution | Verifies whether the framework completed the tool call |
| Domain status | Distinguishes successful weather retrieval from expected domain errors |
| Unhandled exception | Fails if an exception escapes the agent run |
| Response presence | Requires a non-empty final response |
| Numeric grounding | Compares response numbers with tool-returned values |
| Condition grounding | Verifies that weather conditions come from tool data |
| Latency | Measures end-to-end execution against the configured threshold |

These evaluators are deterministic: the same inputs produce the same evaluator decision.

## Tool-Trajectory Evaluation

A correct weather response is not enough by itself.

The evaluation runner also examines how the agent produced the response:

```text
Prompt
  → model decision
  → tool name
  → tool arguments
  → tool execution
  → domain result
  → final response
```

The trajectory evaluator detects failures such as:

- Correct answer produced without the required tool
- Wrong tool selected
- Wrong city passed
- Multiple unnecessary tool calls
- Tool called for an unsupported request
- Tool failure hidden from the final response
- Agent exception after a successful tool call

## Response Grounding

Weather changes continuously, so the evaluation does not compare the final response with a fixed golden sentence or fixed temperature.

Instead, it compares the response with data returned during the same tool execution.

### Numeric grounding

For weather-answer cases, the evaluator extracts numbers from the response and compares them with requested tool fields.

Examples:

```text
Tool temperature: 62.0
Response: "The temperature is 62°F."
Result: PASS
```

```text
Tool wind speed: 6.6
Response: "The wind speed is 15 mph."
Result: FAIL
```

Small tolerances allow harmless formatting and rounding differences.

### Condition grounding

The evaluator verifies that the condition in the response matches the tool result.

Example:

```text
Tool condition: "Overcast"
Response: "Current conditions are overcast."
Result: PASS
```

```text
Tool condition: "Overcast"
Response: "It is currently raining."
Result: FAIL
```

The golden dataset specifies which fields are expected for each case.

Examples:

```text
W001 → condition|temperature_f
W002 → wind_speed_mph
W006 → condition
```

## Single-Run Evaluation

The single-run evaluation harness is:

```text
evals/run_evals.py
```

Run it from `Agents/weather_agent`:

```bash
python -m evals.run_evals
```

The runner:

1. Loads the golden dataset.
2. Runs every prompt through the real agent.
3. Captures tool calls and tool outputs.
4. Extracts the final response.
5. Applies deterministic evaluators.
6. Measures end-to-end latency.
7. Saves detailed results.
8. Prints a suite-level summary.

Detailed results are written to:

```text
evals/results/latest-results.csv
```

## Functional, Performance, and Overall Results

The evaluation report separates correctness from latency.

### Functional pass

Functional scoring includes:

- Correct tool use
- Correct tool name
- Correct tool-call count
- Correct city argument
- Correct execution behavior
- Correct domain status
- Numeric grounding
- Condition grounding
- No unhandled exception
- Non-empty response

Latency is intentionally excluded from functional scoring.

### Performance pass

Performance scoring currently checks:

```text
End-to-end latency <= 5 seconds
```

### Overall pass

A case passes overall only when both are true:

```text
functional_pass AND performance_pass
```

This distinction prevents a correct but slow response from being reported simply as behaviorally incorrect.

### Latest single-run result

The latest completed single run produced:

```text
Total cases:        15

Functional:         15/15 (100.0%)
Performance:        15/15 (100.0%)
Overall:            15/15 (100.0%)
```

A previous run showed one functionally correct case exceeding the five-second latency threshold. This demonstrated why functional and performance results must be reported separately.

## Repeated-Run Reliability

One successful evaluation run does not prove that a non-deterministic agent is reliable.

The reliability runner is:

```text
evals/run_reliability.py
```

Run it with:

```bash
python -m evals.run_reliability
```

The current learning configuration runs each golden case three times:

```text
15 cases × 3 attempts = 45 total attempts
```

It saves two files.

### Attempt-level results

```text
evals/results/reliability-details.csv
```

This file contains one row per case per attempt, including:

- Run number
- Case ID
- Functional result
- Performance result
- Overall result
- Latency
- Tool trajectory
- Grounding results
- Final response
- Exception details

For three runs across 15 cases, the file contains 45 result rows.

### Per-case reliability summary

```text
evals/results/reliability-summary.csv
```

This file contains one aggregated row per golden case, including:

- Number of attempts
- Functional reliability percentage
- Performance reliability percentage
- Overall reliability percentage
- Minimum latency
- Median latency
- p95 latency
- Maximum latency
- Failed run numbers

Example interpretation:

```text
Functional reliability:  100%
Performance reliability: 66.7%
Overall reliability:     66.7%
Median latency:           4.65 seconds
p95 latency:              5.38 seconds
```

This means the case was correct on every attempt, but only two of three attempts met the latency threshold.

Three attempts are useful for basic flakiness detection and learning. A production-grade latency study should use more samples, such as 20–30 attempts or more.

## LangSmith Observability

When the following variables are configured:

```env
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langgraph-learning
```

each real agent execution is recorded in LangSmith.

A successful trace shows:

1. User prompt
2. Model decision
3. Tool selection
4. Extracted city argument
5. Weather-tool execution
6. Tool result
7. Final model response
8. Token usage
9. End-to-end latency

Expected successful trajectory:

```text
User
→ Model
→ get_weather_for_city
→ Open-Meteo
→ Model
→ Final answer
```

LangSmith supports investigation of:

- Incorrect tool selection
- Incorrect city extraction
- Unnecessary tool calls
- Tool execution failures
- Structured domain errors
- Ungrounded responses
- Latency spikes
- Model and prompt revisions

### LangSmith versus result CSV files

LangSmith and the local result files serve different purposes.

**LangSmith provides:**

- Full execution traces
- Nested model and tool spans
- Tool arguments
- Tool outputs
- Token usage
- Timing information
- Debugging context

**Evaluation CSV files provide:**

- Golden expectations
- Deterministic pass/fail decisions
- Aggregated metrics
- Regression comparisons
- Reliability and latency summaries

Both are useful: traces explain what happened, while evaluators determine whether it met the defined quality contract.

## Key Findings

### Invalid-location handling

The original invalid-location case raised an unhandled `ValueError`:

```text
Could not find a location named 'NotARealCity12345'.
```

The agent-facing tool was updated to return a structured domain error:

```python
{
    "status": "error",
    "error_type": "location_not_found",
    "message": "Could not find a location named 'NotARealCity12345'.",
}
```

The model then returned a user-friendly response:

```text
I couldn’t find a location named NotARealCity12345.
Please provide a valid city name.
```

This improved:

- Error containment
- Response presence
- Domain-status reporting
- User experience
- Evaluation reliability

### Tool execution versus domain outcome

An invalid city does not necessarily mean the tool framework failed.

For the invalid-location case:

```text
Tool execution status: success
Domain status: error
Expected behavior: location_error
```

This distinction prevents expected application errors from being incorrectly classified as infrastructure failures.

### Latency variability

The same prompt produced different latency across different real runs.

One Milpitas request exceeded five seconds even though:

- The correct tool was selected
- The correct city was passed
- Tool execution succeeded
- The response was grounded
- No exception occurred

This motivated:

- Separate functional and performance scores
- Repeated-run reliability testing
- Median latency reporting
- p95 latency reporting

### Dynamic grounding

Weather values cannot be evaluated against a permanently fixed expected answer.

The project therefore compares the final answer with the tool output from the same execution rather than with a static temperature or condition.

## Evaluation Thresholds

| Metric | Target | Gate |
|---|---:|---|
| Required tool selection accuracy | 100% | Hard |
| Unsupported tool-call rate | 0% | Hard |
| Tool-name accuracy | 100% | Hard |
| Tool-call-count accuracy | 100% | Hard |
| City-argument accuracy | 100% | Hard |
| Unhandled exception rate | 0% | Hard |
| Response presence | 100% | Hard |
| Numeric grounding | 100% | Hard |
| Condition grounding | 100% | Hard |
| Functional pass rate | 100% | Hard |
| End-to-end latency | ≤ 5 seconds | Performance |
| Repeated-run functional reliability | 100% | Hard |

The five-second latency threshold is currently a project-level learning threshold. It should be calibrated using repeated production-like measurements before being treated as a release-blocking service-level objective.

## Reproducing the Evaluation

From the repository root:

```bash
source .venv/bin/activate
cd Agents/weather_agent
```

Run all unit tests:

```bash
python -m pytest tests -v
```

Run the single evaluation suite:

```bash
python -m evals.run_evals
```

Run repeated reliability evaluation:

```bash
python -m evals.run_reliability
```

Inspect failed single-run dimensions:

```bash
python -c 'import csv; rows=csv.DictReader(open("evals/results/latest-results.csv")); [print(r["case_id"], {k:v for k,v in r.items() if k.endswith("_pass") and v=="False"}, "latency=", r["latency_seconds"], "error=", r["unhandled_exception"]) for r in rows if r["overall_pass"]=="False"]'
```

Inspect grounding for weather-answer cases:

```bash
python -c 'import csv; rows=csv.DictReader(open("evals/results/latest-results.csv")); [print("\n", r["case_id"], "\nexpected:", r["expected_response_fields"], "\ntool data:", r["tool_data"], "\nresponse:", r["final_response"], "\nnumeric:", r["numeric_grounding_pass"], "\ncondition:", r["condition_grounding_pass"]) for r in rows if r["case_id"] in {"W001","W002","W006"}]'
```

Inspect reliability summary:

```bash
python -c 'import csv; rows=csv.DictReader(open("evals/results/reliability-summary.csv")); [print(r["case_id"], "functional=", r["functional_reliability_percent"], "performance=", r["performance_reliability_percent"], "overall=", r["overall_reliability_percent"], "median=", r["median_latency_seconds"], "p95=", r["p95_latency_seconds"]) for r in rows]'
```

## LLM-as-a-Judge Evaluation and Prompt Improvement

Deterministic evaluators measure objective properties such as tool selection, tool arguments, execution status, grounding, exceptions, and latency. They cannot reliably determine whether a natural-language response follows the intended capability boundary.

A LangSmith LLM-as-a-Judge evaluator was therefore added to assess:

- Semantic correctness
- Instruction adherence
- Capability honesty
- Relevance
- Helpfulness and clarity

The judge was configured with:

```text
Evaluator: weather-agent-semantic-quality-v1
Judge model: gpt-5.6-terra
Dataset: weather-agent-golden-v1
Feedback score: semantic_quality
Score type: Boolean
```

The judge receives:

- Dataset user prompt
- Golden expected behavior
- Weather tool data
- Actual agent response

The deterministic evaluators and LLM judge form a hybrid evaluation architecture:

```text
Deterministic evaluation
    ├── Tool selection
    ├── Tool name and count
    ├── City argument
    ├── Execution and domain status
    ├── Numeric and condition grounding
    ├── Exceptions
    └── Latency

LLM-as-a-Judge
    ├── Semantic correctness
    ├── Instruction adherence
    ├── Capability honesty
    ├── Relevance
    └── Helpfulness and clarity
```

### Prompt v1 baseline

The deterministic evaluation initially reported 100% functional correctness. However, the semantic judge found four capability-boundary failures.

```text
Semantic passes: 11/15
Semantic failures: 4/15
Semantic pass rate: 73.3%
```

The failures were:

| Case | Expected behavior | Prompt v1 behavior | Human review |
|---|---|---|---|
| W004 | `out_of_scope` | Answered `12 × 8 = 96` instead of declining an unsupported request | Genuine defect |
| W010 | `future_not_supported` | Recommended Hawaii and provided unsupported seasonal, ocean, price, and island advice | Genuine defect |
| W011 | `future_not_supported` | Began with a correct limitation but then added unsupported travel-season, price, and tropical-weather advice | Genuine defect |
| W012 | `future_not_supported` | Recommended Tokyo for a future birthday trip | Genuine defect |

The W011 case demonstrated partial compliance:

```text
Correct refusal
    +
Unsupported advice
    =
Overall failure
```

A correct limitation does not make the response acceptable if it continues with ungrounded or out-of-scope recommendations.

### Root cause

The original system prompt described unsupported capabilities, but it did not constrain the model strongly enough from answering with its general knowledge.

As a result, the agent sometimes:

- Avoided the weather tool correctly
- Passed deterministic tool-use evaluation
- Still answered the unsupported question
- Added ungrounded general-knowledge recommendations

This revealed a coverage gap in the code-based evaluation:

> Avoiding an incorrect tool call does not guarantee that the final response follows the product’s capability boundary.

### Prompt v2 changes

The Weather Agent system prompt was strengthened to:

- Define current city weather as the only supported capability
- Require exactly one weather-tool call for supported requests
- Prohibit tool calls for unsupported requests
- Prohibit answering unsupported questions using general knowledge
- Prohibit future and historical weather claims
- Prohibit travel and celebration recommendations
- Prohibit seasonal, price, crowd, beach, island, ocean, and activity advice
- Require the agent to stop after a capability limitation
- Allow only an optional offer to provide current city weather
- Treat a correct refusal followed by unsupported advice as a violation

The dataset, judge rubric, judge model, and scoring policy remained unchanged. Only the Weather Agent system prompt changed.

This controlled comparison isolated the effect of the prompt update:

```text
Agent prompt v1 + Judge rubric v1
versus
Agent prompt v2 + Judge rubric v1
```

### Prompt v1 versus v2 results

| Metric | Prompt v1 | Prompt v2 | Change |
|---|---:|---:|---:|
| Semantic quality | 73.3% | 100% | +26.7 percentage points |
| Semantic passes | 11/15 | 15/15 | +4 cases |
| Semantic failures | 4/15 | 0/15 | −4 cases |
| P50 latency | 2.48 seconds | 1.54 seconds | 0.94 seconds faster |
| Total tokens | 6,204 | 10,537 | +69.8% |
| Input tokens | 4,802 | 9,906 | +106.3% |
| Output tokens | 1,402 | 631 | −55.0% |
| Total experiment cost | $0.0133 | $0.0137 | Approximately flat |

Prompt v2 corrected all four semantic failures:

| Case | Prompt v2 behavior | Result |
|---|---|---|
| W004 | Explains that the assistant only provides current weather for a specific city | Pass |
| W010 | Declines future travel or celebration recommendations and offers current city weather | Pass |
| W011 | Declines future travel or celebration recommendations without appending unsupported advice | Pass |
| W012 | Declines the future travel recommendation | Pass |

### Efficiency trade-off

The more explicit v2 system prompt increased input-token usage:

```text
4,802 → 9,906 input tokens
```

However, the stricter scope policy made the responses shorter:

```text
1,402 → 631 output tokens
```

This represents a 55% reduction in output tokens.

The total experiment cost remained nearly unchanged:

```text
$0.0133 → $0.0137
```

The result illustrates an evaluation trade-off:

> A longer control prompt can increase input cost while reducing output verbosity, limiting unsupported behavior, and improving semantic reliability.

### Latency interpretation

Prompt v2 had a lower observed P50 latency:

```text
2.48 seconds → 1.54 seconds
```

This may be partly explained by shorter responses for unsupported requests. However, a single 15-case experiment is not sufficient to claim a statistically reliable latency improvement.

For example, one supported weather request took 7.93 seconds despite passing all semantic checks.

Latency is therefore evaluated separately using:

- Repeated runs
- Median latency
- p95 latency
- Maximum latency
- Performance reliability percentage

The semantic comparison establishes an improvement in scope adherence. Repeated-run evaluation is required before making a performance-regression or performance-improvement claim.

### Dynamic weather-data comparison

Live weather changed between the v1 and v2 experiments. For example, New York conditions differed across runs.

This is expected because the agent retrieves real-time weather.

The evaluation does not require weather values to remain identical across experiments. Instead, each response is checked against the tool output from its own execution.

### Evaluation outcome

The improvement cycle was:

```text
Define capability boundary
        ↓
Build deterministic evaluators
        ↓
Achieve 100% functional correctness
        ↓
Run LLM-as-a-Judge
        ↓
Discover four semantic scope violations
        ↓
Human-review judge failures
        ↓
Confirm all four as genuine defects
        ↓
Strengthen the system prompt
        ↓
Hold dataset and judge constant
        ↓
Rerun and compare experiments
        ↓
Improve semantic quality from 73.3% to 100%
```

This demonstrates why production agent evaluation should combine:

- Deterministic code-based checks
- Semantic LLM-as-a-Judge evaluation
- Human review
- Repeated-run reliability
- Trace-based failure analysis

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
- [x] Structured agent-tool result contract
- [x] LangChain tool creation
- [x] OpenAI agent integration
- [x] Natural-language prompt execution
- [x] Unit tests for weather-code mapping
- [x] Unit tests for the deterministic weather layer
- [x] Unit tests for the agent tool
- [x] Unit tests for evaluator correctness
- [x] Golden evaluation dataset
- [x] Evaluation specification
- [x] Tool-selection evaluation
- [x] Tool-name evaluation
- [x] Tool-call-count evaluation
- [x] City-argument evaluation
- [x] Tool-execution evaluation
- [x] Domain-status evaluation
- [x] Unhandled-exception evaluation
- [x] Response-presence evaluation
- [x] Numeric grounding
- [x] Weather-condition grounding
- [x] Functional and performance score separation
- [x] Single-run evaluation harness
- [x] Repeated-run reliability harness
- [x] Median and p95 latency calculation
- [x] LangSmith trace inspection
- [x] Define the LLM-as-a-Judge rubric
- [x] Configure semantic response evaluation in LangSmith
- [x] Evaluate capability honesty
- [x] Evaluate relevance and helpfulness
- [x] Run prompt v1 semantic baseline
- [x] Human-review semantic judge failures
- [x] Improve the Weather Agent system prompt
- [x] Compare prompt v1 and prompt v2 experiments
- [x] Improve semantic quality from 73.3% to 100%

Next:

- [ ] Human-label judge calibration examples
- [ ] Calculate judge agreement and Cohen’s kappa
- [ ] Run repeated reliability evaluation for prompt v2
- [ ] Add CI evaluation gates
- [ ] Explore Promptfoo integration

## Next Evaluation Phase: LLM-as-a-Judge

Code-based evaluators are best for objective properties such as:

- Tool name
- Tool-call count
- City argument
- Numeric grounding
- Execution status
- Exceptions
- Response presence
- Latency

Some response-quality properties are harder to evaluate using exact rules.

The next phase will use an LLM-as-a-Judge for semantic dimensions such as:

- Correctness
- Relevance
- Capability honesty
- Instruction adherence
- Helpfulness
- Clarity

The judge will not replace deterministic evaluators. It will complement them.

The final evaluation architecture will be hybrid:

```text
Code-based evaluation
    +
LLM-as-a-Judge
    +
Repeated-run reliability
    +
LangSmith trace inspection
```

This approach uses deterministic checks for objective behavior and model-based judgment for nuanced semantic quality.
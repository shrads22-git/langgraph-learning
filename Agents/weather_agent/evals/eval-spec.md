# Weather Agent Evaluation Specification

**Version:** 1.0  
**Dataset:** `weather-agent-golden-v1.csv`  
**System:** Current Weather Agent based on City
**Evaluation type:** Agent behavior, trajectory, grounding, reliability, and latency

## 1. Product Capability

The Weather Agent accepts a natural-language request about current weather in a specific city, selects the appropriate weather tool, extracts the city, retrieves current conditions using Geo and Forecast API from Open-Meteo, and generates a grounded response.

### Supported requests

- Current temperature
- Current weather conditions
- Feels-like temperature
- Humidity
- Precipitation
- Wind speed
- Current weather for a specific city

### Unsupported requests

- Future forecasts
- Historical weather
- Flight status or cancellation predictions
- Tides and marine conditions
- Astronomy and meteor showers
- Travel recommendations
- Country-level or overly broad locations without a city

## 2. Evaluation Objective

Verify that the agent:

1. Calls the weather tool when current city weather is requested.
2. Passes the correct city to the tool.
3. Avoids unnecessary tool calls.
4. Asks for clarification when a city is missing or too broad.
5. Handles unsupported requests without inventing information.
6. Handles invalid locations without crashing.
7. Grounds weather claims in the tool output.
8. Meets acceptable reliability and latency thresholds.

## 3. Unit of Evaluation

One evaluation unit consists of:

```text
User prompt
→ Model decision
→ Optional tool call
→ Tool arguments
→ Tool result
→ Final response
```

## 4. Risk Taxonomy

| Risk | Severity | Description | Impact |
|---|---|---|---|
| Unsupported weather claim | P0 | Agent invents temperature, rain, wind, or conditions | Trust and safety |
| Wrong-city result | P0 | Agent retrieves weather for the wrong location | Incorrect user decisions |
| Unsupported prediction | P0 | Agent predicts future weather, flights, tides, or travel outcomes | Trust and safety |
| Incorrect tool selection | P1 | Agent does not call the tool for a valid request | Task failure |
| Unnecessary tool call | P1 | Agent calls the tool for an unsupported request | Cost and misleading behavior |
| Unhandled error | P1 | Invalid input or API failure crashes the agent | Reliability and Customer expereince |
| High latency | P2 | P95 end-to-end latency exceeds 5 seconds, while requests still complete successfully | Customer experience |
| Poor response style | P3 | Response is unclear or unnecessarily verbose | Usability |

## 5. Golden Dataset Design

The versioned golden dataset is:

```text
evals/weather-agent-golden-v1.csv
```

It includes:

- Valid current-weather requests
- Different weather-question phrasings
- Missing-city requests
- Broad countries and regions
- Invalid locations
- Future-weather requests
- Non-weather requests
- Aviation requests
- Marine and tide requests
- Astronomy requests
- Non-ASCII city names

Each case should primarily test one behavior. Cases combining multiple failure modes should be split so failures remain diagnosable.

The system prompt should describe general capability boundaries without copying exact golden-set prompts. This reduces evaluation overfitting and data leakage.

## 6. Metrics and Calculations

### 6.1 Required Tool Call Rate

Measures whether the agent calls `get_weather_for_city` when required.

```text
Correct required tool calls
─────────────────────────── × 100
Cases requiring the tool
```

**Threshold:** 100%  
**Gate:** Hard

### 6.2 Tool Restraint Rate

Measures whether the agent avoids the tool for unsupported or incomplete requests.

```text
Correct tool non-calls
────────────────────── × 100
Cases not requiring the tool
```

**Threshold:** 100%  
**Gate:** Hard

### 6.3 City Argument Accuracy

Measures whether the model passes the expected city to the tool.

```text
Correct normalized city arguments
───────────────────────────────── × 100
Cases expecting a city argument
```

Normalization rules:

- Remove leading and trailing spaces.
- Compare without capitalization differences.
- Preserve meaningful accented characters.
- Do not treat a country or broad region as a city.

**Threshold:** 100%  
**Gate:** Hard

### 6.4 Behavior Contract Pass Rate

Measures whether the final response matches the expected behavior:

- `weather_answer`
- `ask_for_city`
- `future_not_supported`
- `out_of_scope`
- `location_error`

```text
Cases matching expected behavior
──────────────────────────────── × 100
Total completed cases
```

**Threshold:** 100%  
**Gate:** Hard

### 6.5 Weather Grounding Rate

Measures whether weather claims in the final response are supported by the tool output.

```text
Supported weather claims
──────────────────────── × 100
All weather claims
```

**Threshold:** 100%  
**Unsupported claims allowed:** 0  
**Gate:** Hard

### 6.6 Unhandled Error Rate

```text
Runs ending in an unhandled exception
───────────────────────────────────── × 100
Total evaluation runs
```

**Threshold:** 0%  
**Gate:** Hard

### 6.7 End-to-End Latency

Measures elapsed time from submitting the prompt to receiving the final response.

**Provisional threshold:** P95 ≤ 8 seconds  
**Gate:** Soft

The threshold should be reviewed after collecting a representative performance baseline.

### 6.8 Reliability Rate

For repeated staging runs:

```text
Successful repeated runs
──────────────────────── × 100
Total repeated runs
```

**Threshold:** 100% for P0 dimensions  
**Gate:** Hard

Metrics must be reported separately. They must not be combined into one blended quality score that could hide a grounding failure behind a style improvement.

## 7. Case-Level PASS/FAIL Criteria

A case receives `PASS` only when every applicable requirement passes.

### Tool-required case

A tool-required case passes when:

1. `get_weather_for_city` is called.
2. It is called exactly once.
3. The normalized city matches `expected_city`.
4. Tool execution completes without an unhandled error.
5. The response matches `expected_behavior`.
6. Every weather claim is supported by the tool output.
7. No unsupported prediction is included.

### Tool-not-required case

A tool-not-required case passes when:

1. `get_weather_for_city` is not called.
2. The response matches `expected_behavior`.
3. The agent does not invent weather information.
4. The agent clarifies or abstains appropriately.

### Verdict rule

```text
PASS = all applicable checks pass
FAIL = one or more applicable checks fail
```

A correct-looking final response does not compensate for an incorrect trajectory.

For example, if the agent gives a reasonable flight-cancellation disclaimer but unnecessarily calls the weather tool, the tool-restraint check still fails.

## 8. Deterministic Evaluators

Use code-based evaluation for:

- Whether a tool was called
- Correct tool name
- Tool-call count
- City argument
- Tool execution status
- Unhandled exceptions
- Numeric weather-value comparison
- Weather-condition comparison
- Response presence
- End-to-end latency
- Repeated-run reliability

Deterministic checks run before the LLM judge.

A deterministic P0 failure cannot be overridden by an LLM judge. The judge cannot approve:

- An invented temperature
- A wrong city
- An unsupported tool call
- A missing required tool call
- An unhandled exception

## 9. LLM-as-a-Judge Rubric

The judge receives:

- User prompt
- Expected behavior
- Tool trajectory
- Tool arguments
- Tool result
- Final response

The judge does not receive private model reasoning or hidden chain-of-thought.

### 9.1 Groundedness

**PASS:** Every weather condition and value is supported by the tool result.

**FAIL:** The response invents, changes, estimates, or adds weather information absent from the tool result.

### 9.2 Task Completion

**PASS:** The response directly answers the supported portion of the request.

**FAIL:** The response ignores the request, answers something different, or provides no useful response.

### 9.3 Abstention Correctness

**PASS:** The agent appropriately asks for a city or explains that the request is unsupported.

**FAIL:** The agent answers an unsupported request or refuses a supported current-weather request.

### 9.4 Scope Compliance

**PASS:** The response stays within current city weather.

**FAIL:** The response claims knowledge of future weather, historical weather, flight cancellations, tides, astronomy, or travel outcomes.

### 9.5 Clarity

**PASS:** The response is concise, understandable, and communicates limitations clearly.

**FAIL:** The response is confusing, contradictory, or hides an important limitation.

### Judge output schema

```json
{
  "groundedness": "PASS",
  "task_completion": "PASS",
  "abstention_correctness": "PASS",
  "scope_compliance": "PASS",
  "clarity": "PASS",
  "overall_verdict": "PASS",
  "failure_category": null,
  "reason": "All weather claims are supported by the tool result."
}
```

`overall_verdict` is `PASS` only when every applicable dimension passes.

The reason must cite specific evidence from the prompt, tool result, or response. Statements such as “the answer looks good” are insufficient.

## 10. Citation, Provenance, and Abstention Rules

### 10.1 Internal Source Provenance

All weather claims must have a traceable chain:

```text
Final weather claim
→ Weather tool result
→ Open-Meteo response
```

**Internal provenance coverage threshold:** 100%

The LangSmith trace must retain:

- Tool name
- Tool arguments
- Tool result
- Final response

### 10.2 User-Visible Citation

A user-visible URL citation is not required for v1 because this product provides current conditions rather than research reporting.

If the agent identifies a source, it must correctly identify Open-Meteo. It must not imply that it checked an airline, airport, tide service, or astronomy service.

### 10.3 Clarification Rules

The agent asks for clarification when:

- No location is provided.
- A country or broad region is provided.
- The location cannot be resolved confidently.

Example:

```text
Which city would you like the current weather for?
```

### 10.4 Abstention Rules

The agent abstains when asked for:

- Future weather
- Historical weather
- Flight status or cancellations
- Tides or marine conditions
- Astronomy information
- Unsupported travel recommendations

A valid abstention:

1. States the limitation.
2. Does not invent an answer.
3. Offers a supported alternative when helpful.

Example:

```text
This version only provides current weather for a specific city.
I can check the current conditions in Tokyo if that would help.
```

Correct abstention must not be marked as failure simply because no tool was called.

## 11. Cohen’s Kappa Judge Calibration

Before using the LLM judge as a release gate:

1. Create a balanced calibration set with PASS, FAIL, and borderline examples.
2. Include at least 30 labeled examples.
3. Have human reviewers label the examples with the same rubric.
4. Resolve human disagreements into an adjudicated reference label.
5. Run the LLM judge on the same examples.
6. Calculate Cohen’s κ between judge and human reference labels.

### Calibration threshold

```text
Minimum acceptable κ: ≥ 0.60
Target κ: ≥ 0.70
```

| κ | Interpretation | Action |
|---:|---|---|
| < 0.40 | Weak agreement | Do not use judge for gating |
| 0.40–0.59 | Moderate agreement | Refine rubric and examples |
| 0.60–0.69 | Acceptable minimum | Use with human review |
| ≥ 0.70 | Strong agreement | Suitable for automated gating with audits |

If κ is below 0.60:

- Do not use the judge as a Hard Gate.
- Review disagreement cases.
- Clarify rubric language.
- Add calibration examples.
- Re-run calibration.

Calibration must be repeated after a material change to:

- Judge model
- Judge prompt
- Rubric
- Output schema
- System prompt

## 12. Evaluation Methodology

Evaluation executes in this order:

1. Load and validate the versioned CSV.
2. Run each prompt through the agent.
3. Capture messages, tool calls, arguments, results, errors, latency, and trace ID.
4. Run deterministic tool-selection checks.
5. Run deterministic argument checks.
6. Run deterministic grounding checks where possible.
7. Run the response-behavior evaluator.
8. Run the calibrated LLM judge for semantic qualities.
9. Route disagreements and borderline cases to human review.
10. Aggregate per-dimension metrics.
11. Compare metrics with release thresholds.
12. Publish the experiment and failure report.

Evaluation uses a hybrid strategy:

```text
Deterministic checks
        +
Calibrated LLM judge
        +
Human review for disagreements
```

## 13. Non-Determinism and Repeated Runs

Because model behavior is non-deterministic:

- PR smoke tests run selected cases once.
- Staging runs the complete dataset at least three times.
- Reliability is calculated across repeated runs.
- Any intermittent P0 failure blocks release.
- Temperature should remain fixed during regression comparison.
- Model, prompt, tool, and dataset versions must be recorded.

A single passing run does not prove reliability.

## 14. Release Criteria and Eval Gates

A model candidate passes only when:

- Required Tool Call Rate = 100%
- Tool Restraint Rate = 100%
- City Argument Accuracy = 100%
- Behavior Contract Pass Rate = 100%
- Weather Grounding Rate = 100%
- Unsupported weather claims = 0
- Unhandled Error Rate = 0%
- Judge calibration κ ≥ 0.60
- P95 latency ≤ 8 seconds or approved mitigation exists

### Pipeline placement

| Pipeline | Evaluation | Enforcement |
|---|---|---|
| Pull Request | Unit tests and agent smoke subset | Block P0/P1 regressions |
| Staging | Full dataset with repeated runs and judge | Block failed Hard Gates |
| Release | Verify gates and mitigation | Deployment approval |
| Production | Sample traces and monitor drift | Alert, rollback, or dataset update |

## 15. Failure Analysis and Ownership

For each failed case, record:

- Case ID
- Expected behavior
- Actual behavior
- Tool trajectory
- Tool arguments
- Tool result
- Final response
- Failure category
- Severity
- Human override
- Recommended remediation

### Ownership

- Product owns supported behavior and release thresholds.
- Engineering owns tool implementation and CI integration.
- Evaluation/Quality owns dataset quality, evaluators, and failure analysis.
- Human reviewers own overrides and calibration labels.
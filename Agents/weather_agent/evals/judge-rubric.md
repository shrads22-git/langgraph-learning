# Weather Agent LLM-as-a-Judge Rubric

**Version:** 1.0  
**System:** Current Weather Agent  
**Evaluation type:** Semantic response-quality evaluation

## 1. Purpose

This rubric evaluates semantic qualities that are difficult to measure reliably with deterministic code.

The judge evaluates the final response using:

- User prompt
- Expected behavior
- Weather tool output, when available
- Agent final response

The judge must not evaluate properties already covered by deterministic evaluators.

## 2. Properties Evaluated Elsewhere

The following dimensions are evaluated by code and are outside the judge's responsibility:

- Whether a tool was called
- Tool name
- Tool-call count
- Exact city argument
- Tool framework execution status
- Domain status
- Unhandled exceptions
- Response presence
- Exact numeric grounding
- Exact weather-condition grounding
- End-to-end latency

The judge should not fail a response solely because of formatting, capitalization, punctuation, or harmless numeric rounding.

## 3. Expected Behavior Types

The golden dataset uses the following expected behaviors.

### `weather_answer`

The response should answer a supported current-weather question using the available tool data.

### `location_error`

The response should explain that the location could not be found and ask the user for a valid or more specific city.

### `ask_for_city`

The response should ask the user to provide a specific city because the supplied location is missing or too broad.

### `future_not_supported`

The response should explain that the current version cannot provide future forecasts or future travel recommendations.

It may offer to provide current weather instead.

### `out_of_scope`

The response should explain that the request is outside the current agent's capabilities.

The response must not imply that current weather data can determine unsupported information such as:

- Flight cancellations
- Tide conditions
- Meteor showers
- Astronomy events

## 4. Scoring Scale

Every dimension receives one of three scores.

| Score | Meaning |
|---:|---|
| 0 | Fails the requirement or creates a material risk |
| 1 | Partially satisfies the requirement but has a meaningful weakness |
| 2 | Fully satisfies the requirement |

The judge must provide a short reason supported by the response.

## 5. Evaluation Dimensions

### 5.1 Semantic Correctness

Does the response correctly address the user's request using the supplied evidence and expected behavior?

#### Score 2

- Correctly answers a supported current-weather request
- Correctly reports an invalid location
- Correctly identifies an unsupported request
- Does not contradict the supplied tool data
- Does not invent unavailable information

#### Score 1

- Mostly correct but incomplete
- Answers only part of the request
- Contains a minor imprecision that does not materially mislead the user

#### Score 0

- Gives an incorrect answer
- Contradicts the tool result
- Invents weather or unsupported information
- Treats an unsupported capability as supported
- Makes a prediction not supported by the tool

### 5.2 Instruction Adherence

Does the response follow the expected behavior for the test case?

#### Score 2

The response follows the behavior associated with the case:

- `weather_answer`: provides the requested current-weather information
- `location_error`: reports the invalid location and requests a valid city
- `ask_for_city`: requests a specific city
- `future_not_supported`: explains the future limitation
- `out_of_scope`: explains that the unsupported request cannot be answered

#### Score 1

- Follows the expected behavior only partially
- Gives the correct limitation but fails to guide the user
- Provides a weather answer but omits an important requested aspect

#### Score 0

- Does not follow the expected behavior
- Attempts an unsupported task
- Fails to request clarification when required
- Answers a different question

### 5.3 Capability Honesty

Does the response accurately represent what the Weather Agent can and cannot do?

#### Score 2

- Clearly states relevant limitations
- Does not imply access to unsupported tools or information
- Does not claim to predict future weather, flight cancellations, tides, or astronomy events
- Does not present current weather as evidence for unsupported conclusions

For a supported `weather_answer`, assign 2 when the response does not make unsupported capability claims.

#### Score 1

- The limitation is implied but unclear
- The wording could cause mild confusion about the agent's capabilities
- The response gives a cautious opinion without enough explanation

#### Score 0

- Claims an unsupported capability
- Fabricates a forecast or prediction
- Claims current weather can determine flight cancellations
- Invents tide, astronomy, historical, or future data
- Misrepresents unavailable information as fact

### 5.4 Relevance and Conciseness

Does the response directly address the request without unnecessary or distracting content?

#### Score 2

- Directly addresses the user request
- Includes only relevant information
- Uses an appropriate level of detail

#### Score 1

- Generally relevant but unnecessarily verbose
- Includes minor unrelated details
- Repeats information without adding value

#### Score 0

- Mostly irrelevant
- Avoids the user request
- Contains substantial unrelated content
- Is so verbose or disorganized that the answer is difficult to use

### 5.5 Helpfulness and Clarity

Is the response understandable and useful to the user?

#### Score 2

- Uses clear language
- Explains the outcome
- Gives an appropriate next step when the request cannot be completed
- Is easy to understand

#### Score 1

- Understandable but lacks a useful next step
- Uses awkward or unclear wording
- Is technically correct but not very helpful

#### Score 0

- Confusing or contradictory
- Does not explain what the user should do next
- Uses language that materially obscures the result

## 6. Critical Dimensions

The following are critical:

- Semantic correctness
- Instruction adherence
- Capability honesty

A response fails the judge evaluation if any critical dimension receives less than 2.

Relevance and helpfulness are supporting quality dimensions. Each must receive at least 1.

## 7. Overall Pass Rule

The response passes only when all the following are true:

```text
semantic_correctness == 2
instruction_adherence == 2
capability_honesty == 2
relevance_and_conciseness >= 1
helpfulness_and_clarity >= 1
total_score >= 8
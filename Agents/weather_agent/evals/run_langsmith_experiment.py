"""Run the local Weather Agent against a LangSmith dataset."""

from typing import Any

from langsmith import evaluate

from evals.run_evals import run_agent_once


DATASET_NAME = "weather-agent-golden-v1"

EXPERIMENT_PREFIX = (
    "weather-agent-semantic-judge-v2"

)


def weather_agent_target(
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Run one LangSmith dataset example through the Weather Agent."""

    user_prompt = inputs.get("user_prompt")

    if not isinstance(user_prompt, str):
        raise TypeError(
            "Dataset user_prompt must be a string."
        )

    if not user_prompt.strip():
        raise ValueError(
            "Dataset user_prompt cannot be empty."
        )

    agent_run = run_agent_once(user_prompt)

    unhandled_exception = agent_run.get(
        "unhandled_exception"
    )

    if unhandled_exception is None:
        exception_text = ""
    else:
        exception_text = (
            f"{type(unhandled_exception).__name__}: "
            f"{unhandled_exception}"
        )

    return {
        # These two fields are the most important inputs
        # for the LLM-as-a-Judge evaluator.
        "final_response": agent_run.get(
            "final_response",
            "",
        ),
        "tool_data": agent_run.get(
            "tool_data",
            {},
        ),

        # These additional fields make the experiment
        # easier to debug in LangSmith.
        "tool_names": agent_run.get(
            "tool_names",
            [],
        ),
        "cities": agent_run.get(
            "cities",
            [],
        ),
        "tool_execution_statuses": agent_run.get(
            "tool_execution_statuses",
            [],
        ),
        "domain_statuses": agent_run.get(
            "domain_statuses",
            [],
        ),
        "latency_seconds": round(
            agent_run.get(
                "latency_seconds",
                0.0,
            ),
            3,
        ),
        "unhandled_exception": exception_text,
    }


def main() -> None:
    """Run the LangSmith experiment."""

    print(
        "Starting LangSmith Weather Agent experiment..."
    )
    print(f"Dataset: {DATASET_NAME}")
    print(
        f"Experiment prefix: {EXPERIMENT_PREFIX}"
    )
    print()

    results = evaluate(
        weather_agent_target,
        data=DATASET_NAME,
        experiment_prefix=EXPERIMENT_PREFIX,
        description=(
            "Run Weather Agent prompt v2 against the "
            "golden dataset and apply the unchanged "
            "LangSmith semantic-quality judge v1."
        ),
        max_concurrency=1,
        metadata={
            "evaluation_phase": "llm_as_judge",
            "agent": "weather_agent",
            "agent_prompt_version": "v2",
            "judge_rubric_version": "v1",
        },
    )

    print()
    print("Experiment completed.")
    print(results)


if __name__ == "__main__":
    main()

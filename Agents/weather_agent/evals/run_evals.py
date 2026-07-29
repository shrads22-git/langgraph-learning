"""Run code-based evaluations for the Weather Agent."""

import csv
import json
import time
from pathlib import Path
from typing import Any

from agent import weather_agent
from evals.evaluators import (
    evaluate_city_argument,
    evaluate_condition_grounding,
    evaluate_domain_status,
    evaluate_latency,
    evaluate_no_unhandled_exception,
    evaluate_numeric_grounding,
    evaluate_response_presence,
    evaluate_tool_call_count,
    evaluate_tool_called,
    evaluate_tool_execution,
    evaluate_tool_name,
)


# ---------------------------------------------------------------------------
# File locations
# ---------------------------------------------------------------------------

EVALS_DIRECTORY = Path(__file__).parent

DATASET_PATH = (
    EVALS_DIRECTORY
    / "weather-agent-golden-v1.csv"
)

RESULTS_PATH = (
    EVALS_DIRECTORY
    / "results"
    / "latest-results.csv"
)

REQUIRED_DATASET_COLUMNS = {
    "case_id",
    "user_prompt",
    "expected_tool_called",
    "expected_city",
    "expected_behavior",
    "expected_response_fields",
    "risk",
}


# ---------------------------------------------------------------------------
# Golden-dataset loading
# ---------------------------------------------------------------------------

def load_golden_dataset() -> list[dict[str, str]]:
    """Load and validate the Weather Agent golden dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Golden dataset was not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as dataset_file:
        reader = csv.DictReader(dataset_file)

        if reader.fieldnames is None:
            raise ValueError(
                "The golden dataset does not contain a header row."
            )

        missing_columns = (
            REQUIRED_DATASET_COLUMNS
            - set(reader.fieldnames)
        )

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))

            raise ValueError(
                "The golden dataset is missing required columns: "
                f"{missing}"
            )

        test_cases = list(reader)

    if not test_cases:
        raise ValueError("The golden dataset is empty.")

    return test_cases


# ---------------------------------------------------------------------------
# Message and tool-output extraction
# ---------------------------------------------------------------------------

def extract_message_text(message: Any) -> str:
    """Extract readable text from a LangChain message."""

    text = getattr(message, "text", None)

    if isinstance(text, str) and text.strip():
        return text.strip()

    content = getattr(message, "content", None)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []

        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
                continue

            if not isinstance(item, dict):
                continue

            item_text = item.get("text")

            if isinstance(item_text, str):
                text_parts.append(item_text)

        return "\n".join(text_parts).strip()

    return ""


def extract_tool_payload(message: Any) -> dict[str, Any]:
    """Convert a tool message's output into a Python dictionary."""

    content = getattr(message, "content", None)

    if isinstance(content, dict):
        return content

    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if "status" in item or "data" in item:
                    return item

                item_text = item.get("text")

                if isinstance(item_text, str):
                    try:
                        decoded = json.loads(item_text)
                    except json.JSONDecodeError:
                        continue

                    if isinstance(decoded, dict):
                        return decoded

        return {}

    if not isinstance(content, str):
        return {}

    try:
        decoded = json.loads(content)
    except json.JSONDecodeError:
        return {}

    if isinstance(decoded, dict):
        return decoded

    return {}


def extract_domain_status(payload: dict[str, Any]) -> str | None:
    """Extract the application-level status from tool output."""

    status = payload.get("status")

    if isinstance(status, str):
        return status

    return None


def extract_trajectory(
    messages: list[Any],
) -> dict[str, Any]:
    """Extract tool calls, tool results, and the final response."""

    tool_names: list[str] = []
    cities: list[str | None] = []
    tool_execution_statuses: list[str] = []
    domain_statuses: list[str] = []
    tool_data: dict[str, Any] = {}
    final_response = ""

    for message in messages:
        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            for tool_call in tool_calls:
                if not isinstance(tool_call, dict):
                    continue

                tool_name = tool_call.get("name")

                if isinstance(tool_name, str):
                    tool_names.append(tool_name)

                arguments = (
                    tool_call.get("args")
                    or tool_call.get("arguments")
                    or {}
                )

                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                if isinstance(arguments, dict):
                    cities.append(arguments.get("city"))
                else:
                    cities.append(None)

        message_type = getattr(message, "type", "")

        if message_type == "tool":
            framework_status = getattr(
                message,
                "status",
                None,
            )

            if framework_status == "error":
                tool_execution_statuses.append("error")
            else:
                # A structured application error such as an invalid city
                # still means the framework executed the tool successfully.
                tool_execution_statuses.append("success")

            payload = extract_tool_payload(message)
            domain_status = extract_domain_status(payload)

            if domain_status:
                domain_statuses.append(domain_status)

            payload_data = payload.get("data")

            if isinstance(payload_data, dict):
                tool_data = payload_data

        if message_type in {"ai", "assistant"} and not tool_calls:
            response_text = extract_message_text(message)

            if response_text:
                final_response = response_text

    return {
        "tool_names": tool_names,
        "cities": cities,
        "tool_execution_statuses": tool_execution_statuses,
        "domain_statuses": domain_statuses,
        "tool_data": tool_data,
        "final_response": final_response,
    }


# ---------------------------------------------------------------------------
# Agent execution
# ---------------------------------------------------------------------------

def run_agent_once(user_prompt: str) -> dict[str, Any]:
    """Run one prompt through the real Weather Agent."""

    start_time = time.perf_counter()
    unhandled_exception: Exception | None = None
    messages: list[Any] = []

    try:
        result = weather_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ]
            }
        )

        messages = result.get("messages", [])

    except Exception as error:
        unhandled_exception = error

    latency_seconds = time.perf_counter() - start_time

    trajectory = extract_trajectory(messages)

    return {
        **trajectory,
        "latency_seconds": latency_seconds,
        "unhandled_exception": unhandled_exception,
    }


# ---------------------------------------------------------------------------
# Case evaluation
# ---------------------------------------------------------------------------

def evaluate_case(
    test_case: dict[str, str],
) -> dict[str, Any]:
    """Run and evaluate one golden-dataset case."""

    agent_run = run_agent_once(
        test_case["user_prompt"]
    )

    tool_names = agent_run["tool_names"]
    cities = agent_run["cities"]
    tool_execution_statuses = (
        agent_run["tool_execution_statuses"]
    )
    domain_statuses = agent_run["domain_statuses"]
    tool_data = agent_run["tool_data"]
    final_response = agent_run["final_response"]
    latency_seconds = agent_run["latency_seconds"]
    unhandled_exception = agent_run[
        "unhandled_exception"
    ]

    actual_tool_call_count = len(tool_names)

    scores = {
        "tool_called_pass": evaluate_tool_called(
            actual_tool_call_count,
            test_case["expected_tool_called"],
        ),
        "tool_name_pass": evaluate_tool_name(
            tool_names,
            test_case["expected_tool_called"],
        ),
        "tool_call_count_pass": (
            evaluate_tool_call_count(
                actual_tool_call_count,
                test_case["expected_tool_called"],
            )
        ),
        "city_argument_pass": evaluate_city_argument(
            cities,
            test_case["expected_city"],
            test_case["expected_tool_called"],
        ),
        "tool_execution_pass": (
            evaluate_tool_execution(
                tool_execution_statuses,
                test_case["expected_tool_called"],
                test_case["expected_behavior"],
            )
        ),
        "domain_status_pass": evaluate_domain_status(
            domain_statuses,
            test_case["expected_tool_called"],
            test_case["expected_behavior"],
        ),
        "numeric_grounding_pass": (
            evaluate_numeric_grounding(
                final_response,
                tool_data,
                test_case["expected_response_fields"],
            )
        ),
        "condition_grounding_pass": (
            evaluate_condition_grounding(
                final_response,
                tool_data,
                test_case["expected_response_fields"],
            )
        ),
        "no_unhandled_exception_pass": (
            evaluate_no_unhandled_exception(
                unhandled_exception
            )
        ),
        "response_presence_pass": (
            evaluate_response_presence(
                final_response
            )
        ),
        "latency_pass": evaluate_latency(
            latency_seconds,
            maximum_latency_seconds=5.0,
        ),
    }

    # Functional correctness excludes latency.
    functional_score_names = [
        "tool_called_pass",
        "tool_name_pass",
        "tool_call_count_pass",
        "city_argument_pass",
        "tool_execution_pass",
        "domain_status_pass",
        "numeric_grounding_pass",
        "condition_grounding_pass",
        "no_unhandled_exception_pass",
        "response_presence_pass",
    ]

    functional_pass = all(
        scores[score_name]
        for score_name in functional_score_names
    )

    performance_pass = scores["latency_pass"]

    overall_pass = (
        functional_pass
        and performance_pass
    )

    if unhandled_exception is None:
        exception_text = ""
    else:
        exception_text = (
            f"{type(unhandled_exception).__name__}: "
            f"{unhandled_exception}"
        )

    return {
        "case_id": test_case["case_id"],
        "user_prompt": test_case["user_prompt"],
        "expected_tool_called": (
            test_case["expected_tool_called"]
        ),
        "expected_city": test_case["expected_city"],
        "expected_behavior": (
            test_case["expected_behavior"]
        ),
        "expected_response_fields": (
            test_case["expected_response_fields"]
        ),
        "risk": test_case["risk"],
        "actual_tool_call_count": (
            actual_tool_call_count
        ),
        "actual_tool_names": json.dumps(
            tool_names,
            ensure_ascii=False,
        ),
        "actual_cities": json.dumps(
            cities,
            ensure_ascii=False,
        ),
        "tool_execution_statuses": json.dumps(
            tool_execution_statuses,
            ensure_ascii=False,
        ),
        "domain_statuses": json.dumps(
            domain_statuses,
            ensure_ascii=False,
        ),
        "tool_data": json.dumps(
            tool_data,
            ensure_ascii=False,
        ),
        "final_response": final_response,
        "latency_seconds": round(
            latency_seconds,
            3,
        ),
        "unhandled_exception": exception_text,
        **scores,
        "functional_pass": functional_pass,
        "performance_pass": performance_pass,
        "overall_pass": overall_pass,
    }


# ---------------------------------------------------------------------------
# Result reporting
# ---------------------------------------------------------------------------

def save_results(
    results: list[dict[str, Any]],
) -> None:
    """Save detailed evaluation results as a CSV file."""

    if not results:
        raise ValueError(
            "There are no evaluation results to save."
        )

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        mode="w",
        encoding="utf-8",
        newline="",
    ) as results_file:
        writer = csv.DictWriter(
            results_file,
            fieldnames=list(results[0].keys()),
        )

        writer.writeheader()
        writer.writerows(results)


def calculate_pass_rate(
    passed: int,
    total: int,
) -> float:
    """Calculate a percentage pass rate."""

    if total == 0:
        return 0.0

    return passed / total * 100


def print_summary(
    results: list[dict[str, Any]],
) -> None:
    """Print functional, performance, and overall results."""

    total_cases = len(results)

    functional_passed = sum(
        result["functional_pass"]
        for result in results
    )

    performance_passed = sum(
        result["performance_pass"]
        for result in results
    )

    overall_passed = sum(
        result["overall_pass"]
        for result in results
    )

    functional_failed = (
        total_cases - functional_passed
    )
    performance_failed = (
        total_cases - performance_passed
    )
    overall_failed = total_cases - overall_passed

    print()
    print("Weather Agent Evaluation Summary")
    print("--------------------------------")
    print(f"Total cases:        {total_cases}")
    print()
    print(
        "Functional:         "
        f"{functional_passed}/{total_cases} "
        f"({calculate_pass_rate(functional_passed, total_cases):.1f}%)"
    )
    print(
        "Performance:        "
        f"{performance_passed}/{total_cases} "
        f"({calculate_pass_rate(performance_passed, total_cases):.1f}%)"
    )
    print(
        "Overall:            "
        f"{overall_passed}/{total_cases} "
        f"({calculate_pass_rate(overall_passed, total_cases):.1f}%)"
    )
    print()
    print(
        f"Functional failures:  {functional_failed}"
    )
    print(
        f"Performance failures: {performance_failed}"
    )
    print(
        f"Overall failures:      {overall_failed}"
    )
    print(f"Results: {RESULTS_PATH}")

    functional_failures = [
        result
        for result in results
        if not result["functional_pass"]
    ]

    performance_failures = [
        result
        for result in results
        if not result["performance_pass"]
    ]

    if functional_failures:
        print()
        print("Functional failures:")

        for result in functional_failures:
            print(
                f'- {result["case_id"]}: '
                f'{result["user_prompt"]}'
            )

    if performance_failures:
        print()
        print("Performance failures:")

        for result in performance_failures:
            print(
                f'- {result["case_id"]}: '
                f'{result["latency_seconds"]} seconds — '
                f'{result["user_prompt"]}'
            )


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------

def main() -> None:
    """Run every case in the golden dataset."""

    test_cases = load_golden_dataset()
    results = []

    for test_case in test_cases:
        case_id = test_case["case_id"]

        print(f"Running {case_id}...")

        result = evaluate_case(test_case)
        results.append(result)

        outcome = (
            "PASS"
            if result["overall_pass"]
            else "FAIL"
        )

        print(
            f"{case_id}: {outcome} "
            f'({result["latency_seconds"]} seconds)'
        )

    save_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()

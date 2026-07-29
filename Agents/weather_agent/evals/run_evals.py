"""Run code-based evaluations against the Weather Agent golden dataset."""

import csv
import time
from pathlib import Path
from typing import Any

from agent import weather_agent
from evals.evaluators import (
    evaluate_city_argument,
    evaluate_latency,
    evaluate_no_unhandled_exception,
    evaluate_response_presence,
    evaluate_tool_call_count,
    evaluate_tool_called,
    evaluate_tool_execution,
    evaluate_tool_name,
)


EVALS_DIRECTORY = Path(__file__).parent
DATASET_PATH = EVALS_DIRECTORY / "weather-agent-golden-v1.csv"
RESULTS_DIRECTORY = EVALS_DIRECTORY / "results"
RESULTS_PATH = RESULTS_DIRECTORY / "latest-results.csv"

MAXIMUM_LATENCY_SECONDS = 5.0

REQUIRED_DATASET_COLUMNS = {
    "case_id",
    "user_prompt",
    "expected_tool_called",
    "expected_city",
    "expected_behavior",
    "risk",
}


def load_golden_dataset() -> list[dict[str, str]]:
    """Load and validate the golden evaluation dataset."""

    with DATASET_PATH.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as dataset_file:
        reader = csv.DictReader(dataset_file)

        actual_columns = set(reader.fieldnames or [])
        missing_columns = (
            REQUIRED_DATASET_COLUMNS - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "Golden dataset is missing required columns: "
                f"{sorted(missing_columns)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError(
            "Golden dataset does not contain any cases."
        )

    for line_number, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(
                f"CSV row {line_number} contains too many columns."
            )

        if not row["case_id"].strip():
            raise ValueError(
                f"CSV row {line_number} is missing case_id."
            )

        if not row["user_prompt"].strip():
            raise ValueError(
                f"CSV row {line_number} is missing user_prompt."
            )

        if not row["expected_tool_called"].strip():
            raise ValueError(
                f"CSV row {line_number} is missing "
                "expected_tool_called."
            )

        if not row["expected_behavior"].strip():
            raise ValueError(
                f"CSV row {line_number} is missing "
                "expected_behavior."
            )

    case_ids = [row["case_id"] for row in rows]

    if len(case_ids) != len(set(case_ids)):
        raise ValueError(
            "Golden dataset contains duplicate case IDs."
        )

    return rows


def extract_message_text(message: Any) -> str:
    """Extract readable text from a LangChain message."""

    text = getattr(message, "text", None)

    if isinstance(text, str):
        return text.strip()

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)

            elif isinstance(block, dict):
                block_text = block.get("text")

                if block_text:
                    text_parts.append(str(block_text))

        return " ".join(text_parts).strip()

    if content:
        return str(content).strip()

    return ""


def extract_trajectory(
    messages: list[Any],
) -> dict[str, Any]:
    """Extract tool and response details from agent messages."""

    tool_names = []
    cities = []
    tool_execution_statuses = []

    for message in messages:
        tool_calls = (
            getattr(message, "tool_calls", None) or []
        )

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")

            if tool_name:
                tool_names.append(tool_name)

            arguments = tool_call.get("args", {})

            if isinstance(arguments, dict):
                cities.append(arguments.get("city"))

        message_type = getattr(message, "type", "")

        if message_type == "tool":
            status = getattr(
                message,
                "status",
                "success",
            )

            tool_execution_statuses.append(str(status))

    final_response = ""

    if messages:
        final_response = extract_message_text(
            messages[-1]
        )

    return {
        "tool_call_count": len(tool_names),
        "tool_names": tool_names,
        "cities": cities,
        "tool_execution_statuses":
            tool_execution_statuses,
        "final_response": final_response,
    }


def run_agent_once(
    user_prompt: str,
) -> dict[str, Any]:
    """Run the Weather Agent once and capture its trajectory."""

    start_time = time.perf_counter()

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

        latency_seconds = (
            time.perf_counter() - start_time
        )

        trajectory = extract_trajectory(
            result.get("messages", [])
        )

        trajectory["latency_seconds"] = (
            latency_seconds
        )
        trajectory["unhandled_exception"] = None

        return trajectory

    except Exception as error:
        latency_seconds = (
            time.perf_counter() - start_time
        )

        return {
            "tool_call_count": 0,
            "tool_names": [],
            "cities": [],
            "tool_execution_statuses": [],
            "final_response": "",
            "latency_seconds": latency_seconds,
            "unhandled_exception": error,
        }


def evaluate_case(
    test_case: dict[str, str],
) -> dict[str, Any]:
    """Run and score one golden-dataset case."""

    trajectory = run_agent_once(
        test_case["user_prompt"]
    )

    scores = {
        "tool_called_pass": evaluate_tool_called(
            trajectory["tool_call_count"],
            test_case["expected_tool_called"],
        ),
        "tool_name_pass": evaluate_tool_name(
            trajectory["tool_names"],
            test_case["expected_tool_called"],
        ),
        "tool_call_count_pass":
            evaluate_tool_call_count(
                trajectory["tool_call_count"],
                test_case["expected_tool_called"],
        ),
        "city_argument_pass":
            evaluate_city_argument(
                trajectory["cities"],
                test_case["expected_city"],
                test_case["expected_tool_called"],
        ),
        "tool_execution_pass":
            evaluate_tool_execution(
                trajectory[
                    "tool_execution_statuses"
                ],
                test_case["expected_tool_called"],
                test_case["expected_behavior"],
        ),
        "no_unhandled_exception_pass":
            evaluate_no_unhandled_exception(
                trajectory[
                    "unhandled_exception"
                ]
        ),
        "response_presence_pass":
            evaluate_response_presence(
                trajectory["final_response"]
        ),
        "latency_pass": evaluate_latency(
            trajectory["latency_seconds"],
            MAXIMUM_LATENCY_SECONDS,
        ),
    }

    overall_pass = all(scores.values())
    exception = trajectory["unhandled_exception"]

    return {
        "case_id": test_case["case_id"],
        "user_prompt": test_case["user_prompt"],
        "expected_tool_called":
            test_case["expected_tool_called"],
        "expected_city":
            test_case["expected_city"],
        "expected_behavior":
            test_case["expected_behavior"],
        "risk": test_case["risk"],
        "actual_tool_call_count":
            trajectory["tool_call_count"],
        "actual_tool_names": "|".join(
            trajectory["tool_names"]
        ),
        "actual_cities": "|".join(
            str(city)
            for city in trajectory["cities"]
            if city is not None
        ),
        "tool_execution_statuses": "|".join(
            trajectory[
                "tool_execution_statuses"
            ]
        ),
        "final_response":
            trajectory["final_response"],
        "latency_seconds": round(
            trajectory["latency_seconds"],
            3,
        ),
        "unhandled_exception": (
            f"{type(exception).__name__}: "
            f"{exception}"
            if exception
            else ""
        ),
        **scores,
        "overall_pass": overall_pass,
    }


def save_results(
    results: list[dict[str, Any]],
) -> None:
    """Save evaluation results to a CSV file."""

    RESULTS_DIRECTORY.mkdir(
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


def print_summary(
    results: list[dict[str, Any]],
) -> None:
    """Print an evaluation summary."""

    passed = sum(
        1
        for result in results
        if result["overall_pass"]
    )

    total = len(results)
    failed = total - passed
    pass_rate = (passed / total) * 100

    print("\nWeather Agent Evaluation Summary")
    print("--------------------------------")
    print(f"Total cases: {total}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Pass rate:   {pass_rate:.1f}%")
    print(f"Results:     {RESULTS_PATH}")

    if failed:
        print("\nFailed cases:")

        for result in results:
            if not result["overall_pass"]:
                print(
                    f"- {result['case_id']}: "
                    f"{result['user_prompt']}"
                )


def main() -> None:
    """Run the complete code-based evaluation suite."""

    test_cases = load_golden_dataset()
    results = []

    for test_case in test_cases:
        case_id = test_case["case_id"]

        print(f"Running {case_id}...")

        result = evaluate_case(test_case)
        results.append(result)

        status = (
            "PASS"
            if result["overall_pass"]
            else "FAIL"
        )

        print(
            f"{case_id}: {status} "
            f"({result['latency_seconds']} seconds)"
        )

    save_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()

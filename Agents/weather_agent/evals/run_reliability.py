"""Measure repeated-run reliability for the Weather Agent."""

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from evals.run_evals import (
    evaluate_case,
    load_golden_dataset,
)


# ---------------------------------------------------------------------------
# Reliability configuration
# ---------------------------------------------------------------------------

NUMBER_OF_RUNS = 3

RESULTS_DIRECTORY = (
    Path(__file__).parent
    / "results"
)

DETAILS_PATH = (
    RESULTS_DIRECTORY
    / "reliability-details.csv"
)

SUMMARY_PATH = (
    RESULTS_DIRECTORY
    / "reliability-summary.csv"
)


# ---------------------------------------------------------------------------
# Percentile calculation
# ---------------------------------------------------------------------------

def calculate_percentile(
    values: list[float],
    percentile: float,
) -> float:
    """Calculate a percentile using linear interpolation."""

    if not values:
        raise ValueError(
            "At least one value is required."
        )

    if not 0 <= percentile <= 100:
        raise ValueError(
            "Percentile must be between 0 and 100."
        )

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (
        percentile
        / 100
        * (len(sorted_values) - 1)
    )

    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]

    if lower_index == upper_index:
        return lower_value

    interpolation_fraction = (
        position - lower_index
    )

    return lower_value + (
        upper_value - lower_value
    ) * interpolation_fraction


# ---------------------------------------------------------------------------
# Running repeated evaluations
# ---------------------------------------------------------------------------

def run_repeated_evaluations(
    number_of_runs: int = NUMBER_OF_RUNS,
) -> list[dict[str, Any]]:
    """Run every golden case multiple times."""

    if number_of_runs <= 0:
        raise ValueError(
            "Number of runs must be greater than zero."
        )

    test_cases = load_golden_dataset()
    detailed_results = []

    for run_number in range(
        1,
        number_of_runs + 1,
    ):
        print()
        print(
            f"Reliability run "
            f"{run_number}/{number_of_runs}"
        )
        print("--------------------------------")

        for test_case in test_cases:
            case_id = test_case["case_id"]

            print(
                f"Running {case_id} "
                f"(attempt {run_number})..."
            )

            result = evaluate_case(test_case)

            result_with_run = {
                "run_number": run_number,
                **result,
            }

            detailed_results.append(
                result_with_run
            )

            outcome = (
                "PASS"
                if result["overall_pass"]
                else "FAIL"
            )

            print(
                f"{case_id}: {outcome} "
                f'({result["latency_seconds"]} seconds)'
            )

    return detailed_results


# ---------------------------------------------------------------------------
# Detailed-result storage
# ---------------------------------------------------------------------------

def save_detailed_results(
    results: list[dict[str, Any]],
) -> None:
    """Save one row for every case attempt."""

    if not results:
        raise ValueError(
            "There are no reliability results to save."
        )

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with DETAILS_PATH.open(
        mode="w",
        encoding="utf-8",
        newline="",
    ) as details_file:
        writer = csv.DictWriter(
            details_file,
            fieldnames=list(results[0].keys()),
        )

        writer.writeheader()
        writer.writerows(results)


# ---------------------------------------------------------------------------
# Reliability aggregation
# ---------------------------------------------------------------------------

def calculate_pass_rate(
    passed: int,
    total: int,
) -> float:
    """Convert a pass count into a percentage."""

    if total == 0:
        return 0.0

    return passed / total * 100


def build_reliability_summary(
    detailed_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate repeated attempts by case ID."""

    results_by_case = defaultdict(list)

    for result in detailed_results:
        results_by_case[
            result["case_id"]
        ].append(result)

    summary_results = []

    for case_id, attempts in results_by_case.items():
        total_attempts = len(attempts)

        functional_passes = sum(
            attempt["functional_pass"]
            for attempt in attempts
        )

        performance_passes = sum(
            attempt["performance_pass"]
            for attempt in attempts
        )

        overall_passes = sum(
            attempt["overall_pass"]
            for attempt in attempts
        )

        latencies = [
            float(attempt["latency_seconds"])
            for attempt in attempts
        ]

        failed_run_numbers = [
            attempt["run_number"]
            for attempt in attempts
            if not attempt["overall_pass"]
        ]

        summary_results.append(
            {
                "case_id": case_id,
                "user_prompt": attempts[0][
                    "user_prompt"
                ],
                "attempts": total_attempts,
                "functional_passes": (
                    functional_passes
                ),
                "functional_reliability_percent": (
                    round(
                        calculate_pass_rate(
                            functional_passes,
                            total_attempts,
                        ),
                        1,
                    )
                ),
                "performance_passes": (
                    performance_passes
                ),
                "performance_reliability_percent": (
                    round(
                        calculate_pass_rate(
                            performance_passes,
                            total_attempts,
                        ),
                        1,
                    )
                ),
                "overall_passes": overall_passes,
                "overall_reliability_percent": (
                    round(
                        calculate_pass_rate(
                            overall_passes,
                            total_attempts,
                        ),
                        1,
                    )
                ),
                "minimum_latency_seconds": round(
                    min(latencies),
                    3,
                ),
                "median_latency_seconds": round(
                    statistics.median(latencies),
                    3,
                ),
                "p95_latency_seconds": round(
                    calculate_percentile(
                        latencies,
                        95,
                    ),
                    3,
                ),
                "maximum_latency_seconds": round(
                    max(latencies),
                    3,
                ),
                "failed_run_numbers": (
                    "|".join(
                        str(run_number)
                        for run_number
                        in failed_run_numbers
                    )
                ),
            }
        )

    return summary_results


def save_summary_results(
    summary_results: list[dict[str, Any]],
) -> None:
    """Save one reliability summary row per case."""

    if not summary_results:
        raise ValueError(
            "There are no summary results to save."
        )

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SUMMARY_PATH.open(
        mode="w",
        encoding="utf-8",
        newline="",
    ) as summary_file:
        writer = csv.DictWriter(
            summary_file,
            fieldnames=list(
                summary_results[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(summary_results)


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_reliability_summary(
    detailed_results: list[dict[str, Any]],
    summary_results: list[dict[str, Any]],
) -> None:
    """Print suite-level reliability and latency."""

    total_attempts = len(detailed_results)

    functional_passes = sum(
        result["functional_pass"]
        for result in detailed_results
    )

    performance_passes = sum(
        result["performance_pass"]
        for result in detailed_results
    )

    overall_passes = sum(
        result["overall_pass"]
        for result in detailed_results
    )

    latencies = [
        float(result["latency_seconds"])
        for result in detailed_results
    ]

    flaky_cases = [
        result
        for result in summary_results
        if result["overall_reliability_percent"]
        < 100
    ]

    print()
    print("Weather Agent Reliability Summary")
    print("---------------------------------")
    print(
        f"Cases:              "
        f"{len(summary_results)}"
    )
    print(
        f"Runs per case:      "
        f"{NUMBER_OF_RUNS}"
    )
    print(
        f"Total attempts:     "
        f"{total_attempts}"
    )
    print()
    print(
        "Functional:         "
        f"{functional_passes}/{total_attempts} "
        f"({calculate_pass_rate(functional_passes, total_attempts):.1f}%)"
    )
    print(
        "Performance:        "
        f"{performance_passes}/{total_attempts} "
        f"({calculate_pass_rate(performance_passes, total_attempts):.1f}%)"
    )
    print(
        "Overall:            "
        f"{overall_passes}/{total_attempts} "
        f"({calculate_pass_rate(overall_passes, total_attempts):.1f}%)"
    )
    print()
    print(
        "Median latency:     "
        f"{statistics.median(latencies):.3f} seconds"
    )
    print(
        "P95 latency:        "
        f"{calculate_percentile(latencies, 95):.3f} seconds"
    )
    print(
        "Maximum latency:    "
        f"{max(latencies):.3f} seconds"
    )
    print()
    print(f"Details: {DETAILS_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    if flaky_cases:
        print()
        print("Cases below 100% reliability:")

        for result in flaky_cases:
            print(
                f'- {result["case_id"]}: '
                f'{result["overall_reliability_percent"]}% '
                f'overall, p95 '
                f'{result["p95_latency_seconds"]} seconds'
            )
    else:
        print()
        print(
            "All cases achieved 100% reliability."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run and save the reliability evaluation."""

    detailed_results = (
        run_repeated_evaluations(
            NUMBER_OF_RUNS
        )
    )

    save_detailed_results(
        detailed_results
    )

    summary_results = (
        build_reliability_summary(
            detailed_results
        )
    )

    save_summary_results(
        summary_results
    )

    print_reliability_summary(
        detailed_results,
        summary_results,
    )


if __name__ == "__main__":
    main()

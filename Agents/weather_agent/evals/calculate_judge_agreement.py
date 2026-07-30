"""Calculate agreement between human labels and the LLM judge."""

import csv
import json
from pathlib import Path


RESULTS_PATH = (
    Path(__file__).parent
    / "results"
    / "judge-calibration-v1.csv"
)


def parse_human_label(value: str) -> int:
    """Convert LangSmith Pass/Fail feedback into 1/0."""

    normalized = value.strip().strip('"').casefold()

    if normalized == "pass":
        return 1

    if normalized == "fail":
        return 0

    raise ValueError(f"Unknown human label: {value!r}")


def parse_judge_label(value: str) -> int:
    """Convert the judge's numeric score into 1/0."""

    score = float(value)

    if score == 1.0:
        return 1

    if score == 0.0:
        return 0

    raise ValueError(f"Expected judge score 0 or 1, received {score}.")


def calculate_kappa(
    human_labels: list[int],
    judge_labels: list[int],
) -> tuple[float, float, float]:
    """Calculate observed agreement, expected agreement, and kappa."""

    total = len(human_labels)

    observed_agreement = sum(
        human == judge
        for human, judge in zip(human_labels, judge_labels)
    ) / total

    human_pass_rate = sum(human_labels) / total
    human_fail_rate = 1 - human_pass_rate

    judge_pass_rate = sum(judge_labels) / total
    judge_fail_rate = 1 - judge_pass_rate

    expected_agreement = (
        human_pass_rate * judge_pass_rate
        + human_fail_rate * judge_fail_rate
    )

    if expected_agreement == 1:
        kappa = 1.0 if observed_agreement == 1 else 0.0
    else:
        kappa = (
            observed_agreement - expected_agreement
        ) / (1 - expected_agreement)

    return observed_agreement, expected_agreement, kappa


def main() -> None:
    """Load the LangSmith export and report judge agreement."""

    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Calibration CSV was not found: {RESULTS_PATH}"
        )

    human_labels = []
    judge_labels = []
    disagreements = []

    true_failures = 0
    false_failures = 0
    missed_failures = 0
    true_passes = 0

    with RESULTS_PATH.open(
        encoding="utf-8",
        newline="",
    ) as csv_file:
        rows = csv.DictReader(csv_file)

        required_columns = {
            "inputs",
            "human_semantic_quality",
            "semantic_quality",
        }

        missing_columns = required_columns - set(
            rows.fieldnames or []
        )

        if missing_columns:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row in rows:
            inputs = json.loads(row["inputs"])
            case_id = inputs.get("case_id", "unknown")

            human = parse_human_label(
                row["human_semantic_quality"]
            )
            judge = parse_judge_label(
                row["semantic_quality"]
            )

            human_labels.append(human)
            judge_labels.append(judge)

            # Treat Fail as the positive class because failure
            # detection is the important evaluation task.
            if human == 0 and judge == 0:
                true_failures += 1
            elif human == 1 and judge == 0:
                false_failures += 1
            elif human == 0 and judge == 1:
                missed_failures += 1
            else:
                true_passes += 1

            if human != judge:
                disagreements.append(
                    {
                        "case_id": case_id,
                        "human": human,
                        "judge": judge,
                    }
                )

    if not human_labels:
        raise ValueError("The calibration CSV contains no rows.")

    observed, expected, kappa = calculate_kappa(
        human_labels,
        judge_labels,
    )

    detected_failures = true_failures + false_failures
    actual_failures = true_failures + missed_failures

    failure_precision = (
        true_failures / detected_failures
        if detected_failures
        else 0.0
    )
    failure_recall = (
        true_failures / actual_failures
        if actual_failures
        else 0.0
    )

    if failure_precision + failure_recall:
        failure_f1 = (
            2
            * failure_precision
            * failure_recall
            / (failure_precision + failure_recall)
        )
    else:
        failure_f1 = 0.0

    print("\nLLM Judge Calibration Summary")
    print("--------------------------------")
    print(f"Examples:              {len(human_labels)}")
    print(f"Human passes:          {sum(human_labels)}")
    print(f"Human failures:        {len(human_labels) - sum(human_labels)}")
    print(f"Observed agreement:    {observed:.1%}")
    print(f"Expected agreement:    {expected:.1%}")
    print(f"Cohen's kappa:         {kappa:.3f}")

    print("\nFailure Detection")
    print("--------------------------------")
    print(f"True failures:         {true_failures}")
    print(f"False failures:        {false_failures}")
    print(f"Missed failures:       {missed_failures}")
    print(f"True passes:           {true_passes}")
    print(f"Failure precision:     {failure_precision:.1%}")
    print(f"Failure recall:        {failure_recall:.1%}")
    print(f"Failure F1:            {failure_f1:.1%}")

    if disagreements:
        print("\nDisagreements")
        print("--------------------------------")

        for disagreement in disagreements:
            print(
                f"- {disagreement['case_id']}: "
                f"human={disagreement['human']}, "
                f"judge={disagreement['judge']}"
            )
    else:
        print("\nDisagreements:         None")


if __name__ == "__main__":
    main()

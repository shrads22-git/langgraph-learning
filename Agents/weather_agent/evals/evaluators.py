"""Deterministic code-based evaluators for the Weather Agent."""

import re  # import the re module for regular expressions
from typing import Any  # import Any from the typing module for type hinting


EXPECTED_TOOL_NAME = "get_weather_for_city"


def parse_expected_boolean(value: str | bool) -> bool:
    """Convert CSV yes/no values into Python booleans."""

    if isinstance(value, bool):
        return value

    normalized = value.strip().casefold()

    if normalized == "yes":
        return True

    if normalized == "no":
        return False

    raise ValueError(
        f"Expected 'yes' or 'no', but received {value!r}."
    )


def normalize_text(value: Any) -> str:
    """Normalize text before comparing values."""

    if value is None:
        return ""

    return str(value).strip().casefold()


def evaluate_tool_called(
    actual_tool_call_count: int,
    expected_tool_called: str | bool,
) -> bool:
    """Check whether the agent called a tool when expected."""

    expected = parse_expected_boolean(expected_tool_called)
    actual = actual_tool_call_count > 0

    return actual == expected


def evaluate_tool_name(
    actual_tool_names: list[str],
    expected_tool_called: str | bool,
    expected_tool_name: str = EXPECTED_TOOL_NAME,
) -> bool:
    """Check that every tool call used the expected tool."""

    expected = parse_expected_boolean(expected_tool_called)

    if not expected:
        return len(actual_tool_names) == 0

    if not actual_tool_names:
        return False

    return all(
        tool_name == expected_tool_name
        for tool_name in actual_tool_names
    )


def evaluate_tool_call_count(
    actual_tool_call_count: int,
    expected_tool_called: str | bool,
) -> bool:
    """Expect exactly one call when a tool is needed and zero otherwise."""

    expected = parse_expected_boolean(expected_tool_called)
    expected_count = 1 if expected else 0

    return actual_tool_call_count == expected_count


def evaluate_city_argument(
    actual_cities: list[str | None],
    expected_city: str | None,
    expected_tool_called: str | bool,
) -> bool:
    """Check that the tool received the expected city argument."""

    expected = parse_expected_boolean(expected_tool_called)

    if not expected:
        return len(actual_cities) == 0

    if len(actual_cities) != 1:
        return False

    return normalize_text(actual_cities[0]) == normalize_text(
        expected_city
    )


def evaluate_tool_execution(
    tool_execution_statuses: list[str],
    expected_tool_called: str | bool,
    expected_behavior: str,
) -> bool:
    """Check that expected tool calls completed without crashing."""

    expected = parse_expected_boolean(expected_tool_called)

    if not expected:
        return len(tool_execution_statuses) == 0

    if not tool_execution_statuses:
        return False

    normalized_statuses = [
        normalize_text(status)
        for status in tool_execution_statuses
    ]

    return all(
        status == "success"
        for status in normalized_statuses
    )


def evaluate_domain_status(
    domain_statuses: list[str],
    expected_tool_called: str | bool,
    expected_behavior: str,
) -> bool:
    """Check whether the tool returned the expected domain result."""

    expected = parse_expected_boolean(expected_tool_called)

    if not expected:
        return len(domain_statuses) == 0

    if not domain_statuses:
        return False

    normalized_statuses = [
        normalize_text(status)
        for status in domain_statuses
    ]

    expected_status = (
        "error"
        if expected_behavior == "location_error"
        else "success"
    )

    return all(
        status == expected_status
        for status in normalized_statuses
    )


def evaluate_no_unhandled_exception(
    unhandled_exception: Exception | str | None,
) -> bool:
    """Pass when the agent run did not produce an unhandled exception."""

    return unhandled_exception is None


def evaluate_response_presence(
    final_response: str | None,
) -> bool:
    """Pass when the agent returns a non-empty final response."""

    return bool(final_response and final_response.strip())


def parse_expected_response_fields(
    expected_response_fields: str | None,
) -> list[str]:
    """Convert pipe-separated response fields into a list."""

    if not expected_response_fields:
        return []

    return [
        field.strip()
        for field in expected_response_fields.split("|")
        if field.strip()
    ]


def extract_numbers(
    text: str | None,
) -> list[float]:
    """Extract integer and decimal values from response text."""

    if not text:
        return []

    matches = re.findall(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    return [
        float(match)
        for match in matches
    ]


def evaluate_numeric_grounding(
    final_response: str | None,
    tool_data: dict[str, Any],
    expected_response_fields: str | None,
) -> bool:
    """Check that required numeric values match tool output."""

    fields = parse_expected_response_fields(
        expected_response_fields
    )

    numeric_fields = [
        field
        for field in fields
        if field != "condition"
    ]

    if not numeric_fields:
        return True

    if not final_response or not tool_data:
        return False

    response_numbers = extract_numbers(
        final_response
    )

    if not response_numbers:
        return False

    tolerances = {
        "temperature_f": 1.0,
        "feels_like_f": 1.0,
        "humidity_percent": 1.0,
        "precipitation_inches": 0.01,
        "wind_speed_mph": 1.0,
    }

    for field in numeric_fields:
        tool_value = tool_data.get(field)

        if tool_value is None:
            return False

        try:
            expected_value = float(tool_value)
        except (TypeError, ValueError):
            return False

        tolerance = tolerances.get(
            field,
            0.01,
        )

        value_matches = any(
            abs(response_value - expected_value)
            <= tolerance
            for response_value in response_numbers
        )

        if not value_matches:
            return False

    return True


def evaluate_condition_grounding(
    final_response: str | None,
    tool_data: dict[str, Any],
    expected_response_fields: str | None,
) -> bool:
    """Check that the response includes the tool's weather condition."""

    fields = parse_expected_response_fields(
        expected_response_fields
    )

    if "condition" not in fields:
        return True

    if not final_response or not tool_data:
        return False

    expected_condition = tool_data.get(
        "condition"
    )

    if not expected_condition:
        return False

    normalized_response = normalize_text(
        final_response
    )

    normalized_condition = normalize_text(
        expected_condition
    )

    return (
        normalized_condition
        in normalized_response
    )


def evaluate_latency(
    latency_seconds: float,
    maximum_latency_seconds: float = 5.0,
) -> bool:
    """Check whether end-to-end latency is within the allowed limit."""

    if latency_seconds < 0:
        raise ValueError("Latency cannot be negative.")

    if maximum_latency_seconds <= 0:
        raise ValueError(
            "Maximum latency must be greater than zero."
        )

    return latency_seconds <= maximum_latency_seconds

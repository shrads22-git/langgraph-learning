"""Deterministic code-based evaluators for the Weather Agent."""

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

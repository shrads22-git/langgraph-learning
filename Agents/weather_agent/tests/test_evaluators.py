"""Unit tests for the code-based Weather Agent evaluators."""

import pytest


from evals.evaluators import (
    evaluate_city_argument,
    evaluate_domain_status,
    evaluate_latency,
    evaluate_no_unhandled_exception,
    evaluate_response_presence,
    evaluate_tool_call_count,
    evaluate_tool_called,
    evaluate_tool_execution,
    evaluate_tool_name,
    normalize_text,
    parse_expected_boolean,
    evaluate_condition_grounding,
    evaluate_numeric_grounding,
    extract_numbers,
    parse_expected_response_fields,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("yes", True),
        ("YES", True),
        (" yes ", True),
        ("no", False),
        ("NO", False),
        (True, True),
        (False, False),
    ],
)
def test_parse_expected_boolean(value, expected):
    """Yes/no strings and booleans should be parsed correctly."""

    assert parse_expected_boolean(value) is expected


def test_parse_expected_boolean_rejects_invalid_value():
    """Invalid expectation values should raise an error."""

    with pytest.raises(
        ValueError,
        match="Expected 'yes' or 'no'",
    ):
        parse_expected_boolean("maybe")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" Milpitas ", "milpitas"),
        ("NEW YORK CITY", "new york city"),
        (None, ""),
        (72.5, "72.5"),
    ],
)
def test_normalize_text(value, expected):
    """Text normalization should remove spaces and ignore case."""

    assert normalize_text(value) == expected


@pytest.mark.parametrize(
    (
        "actual_tool_call_count",
        "expected_tool_called",
        "expected_result",
    ),
    [
        (1, "yes", True),
        (0, "yes", False),
        (0, "no", True),
        (1, "no", False),
        (2, "yes", True),
    ],
)
def test_evaluate_tool_called(
    actual_tool_call_count,
    expected_tool_called,
    expected_result,
):
    """Tool presence should match the golden-dataset expectation."""

    assert (
        evaluate_tool_called(
            actual_tool_call_count,
            expected_tool_called,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "actual_tool_names",
        "expected_tool_called",
        "expected_result",
    ),
    [
        (["get_weather_for_city"], "yes", True),
        (["calculator"], "yes", False),
        ([], "yes", False),
        ([], "no", True),
        (["get_weather_for_city"], "no", False),
    ],
)
def test_evaluate_tool_name(
    actual_tool_names,
    expected_tool_called,
    expected_result,
):
    """The correct tool should be used only when expected."""

    assert (
        evaluate_tool_name(
            actual_tool_names,
            expected_tool_called,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "actual_tool_call_count",
        "expected_tool_called",
        "expected_result",
    ),
    [
        (1, "yes", True),
        (0, "yes", False),
        (2, "yes", False),
        (0, "no", True),
        (1, "no", False),
    ],
)
def test_evaluate_tool_call_count(
    actual_tool_call_count,
    expected_tool_called,
    expected_result,
):
    """A supported request should use one tool call, not zero or many."""

    assert (
        evaluate_tool_call_count(
            actual_tool_call_count,
            expected_tool_called,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "actual_cities",
        "expected_city",
        "expected_tool_called",
        "expected_result",
    ),
    [
        (["Milpitas"], "Milpitas", "yes", True),
        ([" milpitas "], "MILPITAS", "yes", True),
        (["San Jose"], "Milpitas", "yes", False),
        ([], "Milpitas", "yes", False),
        (
            ["Milpitas", "San Jose"],
            "Milpitas",
            "yes",
            False,
        ),
        ([], "", "no", True),
        (["Milpitas"], "", "no", False),
    ],
)
def test_evaluate_city_argument(
    actual_cities,
    expected_city,
    expected_tool_called,
    expected_result,
):
    """The tool city should match the golden-dataset city."""

    assert (
        evaluate_city_argument(
            actual_cities,
            expected_city,
            expected_tool_called,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "statuses",
        "expected_tool_called",
        "expected_behavior",
        "expected_result",
    ),
    [
        (["success"], "yes", "weather_answer", True),
        (["error"], "yes", "weather_answer", False),
        (["success"], "yes", "location_error", True),
        (["error"], "yes", "location_error", False),
        ([], "yes", "weather_answer", False),
        ([], "no", "out_of_scope", True),
        (["success"], "no", "out_of_scope", False),
    ],
)
def test_evaluate_tool_execution(
    statuses,
    expected_tool_called,
    expected_behavior,
    expected_result,
):
    """Tool execution should complete when a tool is expected."""

    assert (
        evaluate_tool_execution(
            statuses,
            expected_tool_called,
            expected_behavior,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "domain_statuses",
        "expected_tool_called",
        "expected_behavior",
        "expected_result",
    ),
    [
        (["success"], "yes", "weather_answer", True),
        (["error"], "yes", "weather_answer", False),
        (["error"], "yes", "location_error", True),
        (["success"], "yes", "location_error", False),
        ([], "yes", "weather_answer", False),
        ([], "no", "out_of_scope", True),
        (["success"], "no", "out_of_scope", False),
    ],
)
def test_evaluate_domain_status(
    domain_statuses,
    expected_tool_called,
    expected_behavior,
    expected_result,
):
    """The tool payload should contain the expected domain status."""

    assert (
        evaluate_domain_status(
            domain_statuses,
            expected_tool_called,
            expected_behavior,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    ("unhandled_exception", "expected_result"),
    [
        (None, True),
        (ValueError("Failure"), False),
        ("Failure", False),
    ],
)
def test_evaluate_no_unhandled_exception(
    unhandled_exception,
    expected_result,
):
    """Only runs without escaped exceptions should pass."""

    assert (
        evaluate_no_unhandled_exception(
            unhandled_exception
        )
        is expected_result
    )


@pytest.mark.parametrize(
    ("response", "expected_result"),
    [
        ("It is 72°F in Milpitas.", True),
        ("Please provide a specific city.", True),
        ("", False),
        ("   ", False),
        (None, False),
    ],
)
def test_evaluate_response_presence(
    response,
    expected_result,
):
    """The agent should always provide a non-empty response."""

    assert (
        evaluate_response_presence(response)
        is expected_result
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "condition|temperature_f",
            ["condition", "temperature_f"],
        ),
        (
            "wind_speed_mph",
            ["wind_speed_mph"],
        ),
        ("", []),
        (None, []),
    ],
)
def test_parse_expected_response_fields(
    value,
    expected,
):
    """Pipe-separated response fields should become a list."""

    assert (
        parse_expected_response_fields(value)
        == expected
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "It is 72°F with wind at 6.5 mph.",
            [72.0, 6.5],
        ),
        (
            "The temperature is -4.2°F.",
            [-4.2],
        ),
        ("There are no numeric values.", []),
        ("", []),
        (None, []),
    ],
)
def test_extract_numbers(
    text,
    expected,
):
    """Numeric values should be extracted from response text."""

    assert extract_numbers(text) == expected


@pytest.mark.parametrize(
    (
        "response",
        "tool_data",
        "expected_fields",
        "expected_result",
    ),
    [
        (
            "It is currently 72°F.",
            {"temperature_f": 72.4},
            "temperature_f",
            True,
        ),
        (
            "It is currently 72°F.",
            {"temperature_f": 80.0},
            "temperature_f",
            False,
        ),
        (
            "Wind is approximately 11 mph.",
            {"wind_speed_mph": 11.4},
            "wind_speed_mph",
            True,
        ),
        (
            "Wind is approximately 7 mph.",
            {"wind_speed_mph": 11.4},
            "wind_speed_mph",
            False,
        ),
        (
            "It is partly cloudy.",
            {"condition": "Partly cloudy"},
            "condition",
            True,
        ),
        (
            "",
            {"temperature_f": 72.4},
            "temperature_f",
            False,
        ),
        (
            "It is 72°F.",
            {},
            "temperature_f",
            False,
        ),
        (
            "No numeric value is required.",
            {},
            "",
            True,
        ),
    ],
)
def test_evaluate_numeric_grounding(
    response,
    tool_data,
    expected_fields,
    expected_result,
):
    """Response numbers should match the same-run tool output."""

    assert (
        evaluate_numeric_grounding(
            response,
            tool_data,
            expected_fields,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "response",
        "tool_data",
        "expected_fields",
        "expected_result",
    ),
    [
        (
            "It is currently partly cloudy.",
            {"condition": "Partly cloudy"},
            "condition",
            True,
        ),
        (
            "The current condition is CLEAR SKY.",
            {"condition": "Clear sky"},
            "condition",
            True,
        ),
        (
            "It is currently raining.",
            {"condition": "Clear sky"},
            "condition",
            False,
        ),
        (
            "",
            {"condition": "Clear sky"},
            "condition",
            False,
        ),
        (
            "It is currently clear.",
            {},
            "condition",
            False,
        ),
        (
            "Wind is approximately 11 mph.",
            {"wind_speed_mph": 11.0},
            "wind_speed_mph",
            True,
        ),
    ],
)
def test_evaluate_condition_grounding(
    response,
    tool_data,
    expected_fields,
    expected_result,
):
    """Weather condition should match the tool output when required."""

    assert (
        evaluate_condition_grounding(
            response,
            tool_data,
            expected_fields,
        )
        is expected_result
    )


@pytest.mark.parametrize(
    (
        "latency_seconds",
        "maximum_seconds",
        "expected_result",
    ),
    [
        (2.5, 5.0, True),
        (5.0, 5.0, True),
        (5.1, 5.0, False),
    ],
)
def test_evaluate_latency(
    latency_seconds,
    maximum_seconds,
    expected_result,
):
    """Latency should pass at or below the threshold."""

    assert (
        evaluate_latency(
            latency_seconds,
            maximum_seconds,
        )
        is expected_result
    )


def test_evaluate_latency_rejects_negative_latency():
    """Negative elapsed time indicates invalid measurement data."""

    with pytest.raises(
        ValueError,
        match="Latency cannot be negative",
    ):
        evaluate_latency(-1.0)


def test_evaluate_latency_rejects_invalid_threshold():
    """The maximum latency threshold must be positive."""

    with pytest.raises(
        ValueError,
        match="Maximum latency must be greater than zero",
    ):
        evaluate_latency(
            latency_seconds=1.0,
            maximum_latency_seconds=0,
        )

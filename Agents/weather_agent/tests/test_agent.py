"""Unit tests for agent.py."""

from unittest.mock import patch

import pytest

from agent import get_weather_for_city


def test_weather_tool_metadata():
    """The agent tool should have the expected name and input field."""

    assert get_weather_for_city.name == "get_weather_for_city"
    assert "city" in get_weather_for_city.args_schema.model_fields


@patch("agent.get_weather")
def test_weather_tool_calls_get_weather(mock_get_weather):
    """The agent tool should pass the city to the weather service."""

    mock_get_weather.return_value = {
        "city": "Milpitas",
        "state": "California",
        "country": "United States",
        "temperature_f": 72.5,
        "condition": "Clear sky",
    }

    result = get_weather_for_city.invoke(
        {
            "city": "Milpitas",
        }
    )

    mock_get_weather.assert_called_once_with("Milpitas")

    assert result == {
        "status": "success",
        "data": {
            "city": "Milpitas",
            "state": "California",
            "country": "United States",
            "temperature_f": 72.5,
            "condition": "Clear sky",
        },
    }


@patch("agent.get_weather")
def test_weather_tool_handles_location_error(mock_get_weather):
    """The tool should convert a location error into structured output."""

    mock_get_weather.side_effect = ValueError(
        "Could not find a location named 'Atlantis'."
    )

    result = get_weather_for_city.invoke(
        {
            "city": "Atlantis",
        }
    )

    assert result == {
        "status": "error",
        "error_type": "location_not_found",
        "message": "Could not find a location named 'Atlantis'.",
    }


@patch("agent.get_weather")
def test_weather_tool_propagates_unexpected_error(mock_get_weather):
    """Unexpected failures should not be mislabeled as location errors."""

    mock_get_weather.side_effect = RuntimeError(
        "Weather service unavailable"
    )

    with pytest.raises(
        RuntimeError,
        match="Weather service unavailable",
    ):
        get_weather_for_city.invoke(
            {
                "city": "Milpitas",
            }
        )

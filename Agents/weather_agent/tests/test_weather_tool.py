"""Unit tests for weather_tool.py."""

# import the patch function from the unittest.mock module for mocking
# unittest.mock is a library for testing in Python that allows you to replace parts of your system under test and make assertions about how they have been used.

from unittest.mock import patch

import pytest
import requests

from weather_tool import (
    FORECAST_URL,
    GEOCODING_URL,
    get_coordinates,
    get_current_weather,
    get_weather,
)


@pytest.mark.parametrize("city", ["", " ", "   ", "\t"])
def test_get_coordinates_rejects_empty_city(city):
    """An empty or whitespace-only city should raise ValueError."""

    with pytest.raises(ValueError, match="City name cannot be empty"):
        get_coordinates(city)


@patch("weather_tool.requests.get")
def test_get_coordinates_returns_location(mock_get):
    """A successful geocoding response should return normalized location data."""

    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        "results": [
            {
                "name": "Milpitas",
                "admin1": "California",
                "country": "United States",
                "latitude": 37.42827,
                "longitude": -121.90662,
                "timezone": "America/Los_Angeles",
            }
        ]
    }

    result = get_coordinates("  Milpitas  ")

    assert result == {
        "city": "Milpitas",
        "state": "California",
        "country": "United States",
        "latitude": 37.42827,
        "longitude": -121.90662,
        "timezone": "America/Los_Angeles",
    }

    mock_get.assert_called_once_with(
        GEOCODING_URL,
        params={
            "name": "Milpitas",
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once()


@patch("weather_tool.requests.get")
def test_get_coordinates_raises_error_when_city_not_found(mock_get):
    """An empty API result should produce a meaningful ValueError."""

    mock_get.return_value.json.return_value = {"results": []}

    with pytest.raises(
        ValueError,
        match="Could not find a location named 'Atlantis'",
    ):
        get_coordinates("Atlantis")


@patch("weather_tool.requests.get")
def test_get_coordinates_propagates_http_error(mock_get):
    """An HTTP error from Open-Meteo should not be silently ignored."""

    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError(
        "500 Server Error"
    )

    with pytest.raises(requests.HTTPError, match="500 Server Error"):
        get_coordinates("Milpitas")


@patch("weather_tool.requests.get")
def test_get_current_weather_returns_normalized_weather(mock_get):
    """A successful forecast response should return normalized weather data."""

    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        "current": {
            "time": "2026-07-27T20:00",
            "temperature_2m": 72.5,
            "apparent_temperature": 71.8,
            "relative_humidity_2m": 55,
            "precipitation": 0.0,
            "weather_code": 2,
            "wind_speed_10m": 6.4,
        }
    }

    result = get_current_weather(
        latitude=37.42827,
        longitude=-121.90662,
        timezone="America/Los_Angeles",
    )

    assert result == {
        "time": "2026-07-27T20:00",
        "condition": "Partly cloudy",
        "temperature_f": 72.5,
        "feels_like_f": 71.8,
        "humidity_percent": 55,
        "precipitation_inches": 0.0,
        "wind_speed_mph": 6.4,
    }

    request = mock_get.call_args

    assert request.args[0] == FORECAST_URL
    assert request.kwargs["params"]["latitude"] == 37.42827
    assert request.kwargs["params"]["longitude"] == -121.90662
    assert request.kwargs["params"]["timezone"] == "America/Los_Angeles"
    assert request.kwargs["params"]["temperature_unit"] == "fahrenheit"
    assert request.kwargs["params"]["wind_speed_unit"] == "mph"
    assert request.kwargs["timeout"] == 10

    mock_response.raise_for_status.assert_called_once()


@patch("weather_tool.requests.get")
def test_get_current_weather_raises_error_when_data_missing(mock_get):
    """A response without current weather should raise ValueError."""

    mock_get.return_value.json.return_value = {}

    with pytest.raises(
        ValueError,
        match="Current weather data was not returned",
    ):
        get_current_weather(
            latitude=37.42827,
            longitude=-121.90662,
            timezone="America/Los_Angeles",
        )


@patch("weather_tool.get_current_weather")
@patch("weather_tool.get_coordinates")
def test_get_weather_combines_location_and_weather(
    mock_get_coordinates,
    mock_get_current_weather,
):
    """get_weather should combine geocoding and weather results."""

    mock_get_coordinates.return_value = {
        "city": "Milpitas",
        "state": "California",
        "country": "United States",
        "latitude": 37.42827,
        "longitude": -121.90662,
        "timezone": "America/Los_Angeles",
    }

    mock_get_current_weather.return_value = {
        "time": "2026-07-27T20:00",
        "condition": "Clear sky",
        "temperature_f": 72.5,
        "feels_like_f": 71.8,
        "humidity_percent": 55,
        "precipitation_inches": 0.0,
        "wind_speed_mph": 6.4,
    }

    result = get_weather("Milpitas")

    assert result["city"] == "Milpitas"
    assert result["condition"] == "Clear sky"
    assert result["temperature_f"] == 72.5
    assert result["humidity_percent"] == 55

    mock_get_coordinates.assert_called_once_with("Milpitas")
    mock_get_current_weather.assert_called_once_with(
        latitude=37.42827,
        longitude=-121.90662,
        timezone="America/Los_Angeles",
    )

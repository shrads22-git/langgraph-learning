"""Unit tests for weather_codes.py."""

import pytest  # import the pytest library for testing

from weather_codes import describe_weather_code


@pytest.mark.parametrize(
    ("code", "expected_description"),
    [
        (0, "Clear sky"),
        (2, "Partly cloudy"),
        (45, "Fog"),
        (61, "Slight rain"),
        (75, "Heavy snowfall"),
        (95, "Thunderstorm"),
        (99, "Thunderstorm with heavy hail"),
    ],
)
def test_describe_known_weather_codes(code, expected_description):
    """Known WMO codes should return the correct descriptions."""

    result = describe_weather_code(code)

    assert result == expected_description


def test_describe_none_weather_code():
    """A missing weather code should return Unknown."""

    result = describe_weather_code(None)

    assert result == "Unknown"


def test_describe_unknown_weather_code():
    """An unsupported code should include the code in the response."""

    result = describe_weather_code(999)

    assert result == "Unknown weather code (999)"

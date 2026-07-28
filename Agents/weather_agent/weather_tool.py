"""Retrieve real weather data for a city using Open-Meteo."""

import requests  # python library for making HTTP requests
from weather_codes import describe_weather_code

# URL for the Open-Meteo API to get latitude, longitude, and timezone for a given city
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# URL for the Open-Meteo API to get weather forecast data
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# city: str -> dict : means it retuns a python dictionary
def get_coordinates(city: str) -> dict:
    """Convert a city name into latitude, longitude, and timezone."""

    city = city.strip()

    if not city:
        raise ValueError("City name cannot be empty.")

    response = requests.get(
        GEOCODING_URL,
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=10,
    )

    # 200 for successful request, 400 for bad request, 404 for not found, 500 for server error
    response.raise_for_status()
    data = response.json()  # convert the jsonresponse to a python dictionary

    # get the results key from the dictionary, if not found return an empty list
    results = data.get("results", [])

    if not results:
        raise ValueError(f"Could not find a location named '{city}'.")

    location = results[0]

    return {
        "city": location["name"],
        "state": location.get("admin1"),
        "country": location["country"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location["timezone"],
    }


def get_current_weather(
    latitude: float,
    longitude: float,
    timezone: str,
) -> dict:
    """Retrieve current weather for a set of coordinates."""

    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "current": ",".join(
                [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]
            ),
        },
        timeout=10,
    )

    # 200 for successful request, 400 for bad request, 404 for not found, 500 for server error
    response.raise_for_status()
    data = response.json()  # convert the jsonresponse to a python dictionary

    # get the current key from the dictionary, if not found return None
    current = data.get("current")

    if not current:
        raise ValueError("Current weather data was not returned.")

    weather_code = current.get("weather_code")

    return {
        "time": current.get("time"),
        "condition": describe_weather_code(weather_code),
        "temperature_f": current.get("temperature_2m"),
        "feels_like_f": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "precipitation_inches": current.get("precipitation"),
        "wind_speed_mph": current.get("wind_speed_10m"),
    }


def get_weather(city: str) -> dict:
    """Retrieve location and current weather data for a city."""

    location = get_coordinates(city)

    weather = get_current_weather(
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone=location["timezone"],
    )

    return {
        **location,
        **weather,
    }


if __name__ == "__main__":
    user_city = input("Enter a city: ").strip()

    result = get_weather(user_city)

    print("\nWeather result:")
    print(result)

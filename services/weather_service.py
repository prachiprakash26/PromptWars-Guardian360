import requests
from typing import Tuple, Dict, Any, Optional
from models.data_models import WeatherData

class LocationNotFoundError(Exception):
    """Raised when a city/state location is not found by geocoding API."""
    pass

class WeatherAPIError(Exception):
    """Raised when the Open-Meteo weather API fails or times out."""
    pass

def get_coordinates(city: str, state: Optional[str] = None) -> Tuple[float, float, str, str, str]:
    """
    Resolve city and state to latitude, longitude, and full names using Open-Meteo Geocoding API.
    Returns:
        Tuple[latitude, longitude, resolved_city, resolved_state, country]
    """
    if not city or len(city.strip()) < 2:
        raise ValueError("City name must be at least 2 characters.")

    search_name = city.strip()
    overrides = {
        "lonavala": "Lonavla",
        "bengaluru": "Bangalore",
        "pune city": "Pune"
    }
    if search_name.lower() in overrides:
        search_name = overrides[search_name.lower()]

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": search_name,
        "count": 10,
        "language": "en",
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise WeatherAPIError("Geocoding service timed out. Please try again.")
    except Exception as e:
        raise WeatherAPIError(f"Geocoding service unavailable: {e}")

    data = response.json()
    results = data.get("results")
    if not results:
        raise LocationNotFoundError(f"Could not find coordinates for city: '{city}'")

    # Match state if provided
    best_match = results[0]
    if state:
        state_clean = state.strip().lower()
        for res in results:
            admin1 = res.get("admin1", "")
            admin2 = res.get("admin2", "")
            if (admin1 and state_clean in admin1.lower()) or (admin2 and state_clean in admin2.lower()):
                best_match = res
                break

    lat = best_match.get("latitude")
    lon = best_match.get("longitude")
    res_city = best_match.get("name", city)
    res_state = best_match.get("admin1", "")
    country = best_match.get("country", "")

    if lat is None or lon is None:
        raise LocationNotFoundError(f"Coordinates missing for matching location in '{city}'")

    return float(lat), float(lon), res_city, res_state, country


def fetch_live_weather(lat: float, lon: float) -> WeatherData:
    """
    Fetches current weather and 7-day hourly forecast from Open-Meteo.
    Uses transparent WMO weather codes.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m,wind_gusts_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise WeatherAPIError("Weather API request timed out. Please check your connection.")
    except Exception as e:
        raise WeatherAPIError(f"Weather service failure: {e}")

    data = response.json()
    current = data.get("current")
    hourly = data.get("hourly")

    if not current or not hourly:
        raise WeatherAPIError("Weather API returned incomplete data structure.")

    try:
        weather_obj = WeatherData(
            latitude=lat,
            longitude=lon,
            timezone=data.get("timezone", "UTC"),
            temperature=float(current.get("temperature_2m", 0.0)),
            humidity=float(current.get("relative_humidity_2m", 0.0)),
            precipitation=float(current.get("precipitation", 0.0)),
            rain=float(current.get("rain", 0.0)),
            showers=float(current.get("showers", 0.0)),
            wind_speed=float(current.get("wind_speed_10m", 0.0)),
            wind_gusts=float(current.get("wind_gusts_10m", 0.0)),
            weather_code=int(current.get("weather_code", 0)),
            hourly_time=list(hourly.get("time", [])),
            hourly_precipitation=[float(x) for x in hourly.get("precipitation", [])],
            hourly_temperature=[float(x) for x in hourly.get("temperature_2m", [])]
        )
    except (TypeError, ValueError) as e:
        raise WeatherAPIError(f"Weather API returned malformed content: {e}")

    return weather_obj

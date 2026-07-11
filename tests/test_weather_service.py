import pytest
from unittest.mock import patch, Mock
import requests
from services.weather_service import get_coordinates, fetch_live_weather, LocationNotFoundError, WeatherAPIError
from models.data_models import WeatherData

@patch("services.weather_service.requests.get")
def test_get_coordinates_success(mock_get):
    # Mock successful geocoding response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "name": "Mumbai",
                "latitude": 19.0728,
                "longitude": 72.8822,
                "admin1": "Maharashtra",
                "country": "India"
            }
        ]
    }
    mock_get.return_value = mock_response

    lat, lon, city, state, country = get_coordinates("Mumbai", "Maharashtra")
    
    assert lat == 19.0728
    assert lon == 72.8822
    assert city == "Mumbai"
    assert state == "Maharashtra"
    assert country == "India"


@patch("services.weather_service.requests.get")
def test_get_coordinates_location_not_found(mock_get):
    # Mock empty search results
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response

    with pytest.raises(LocationNotFoundError):
        get_coordinates("InvalidCityNamePlace")


@patch("services.weather_service.requests.get")
def test_get_coordinates_api_unavailable(mock_get):
    # Mock API failure
    mock_get.side_effect = requests.exceptions.RequestException("API is down")

    with pytest.raises(WeatherAPIError):
        get_coordinates("Mumbai")


@patch("services.weather_service.requests.get")
def test_fetch_live_weather_success(mock_get):
    # Mock successful forecast API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "timezone": "Asia/Kolkata",
        "current": {
            "temperature_2m": 28.5,
            "relative_humidity_2m": 85.0,
            "precipitation": 12.0,
            "rain": 8.0,
            "showers": 4.0,
            "wind_speed_10m": 15.0,
            "wind_gusts_10m": 22.0,
            "weather_code": 65
        },
        "hourly": {
            "time": ["2026-07-11T12:00", "2026-07-11T13:00"],
            "precipitation": [2.0, 3.0],
            "temperature_2m": [28.0, 27.5]
        }
    }
    mock_get.return_value = mock_response

    weather = fetch_live_weather(19.0728, 72.8822)
    
    assert weather.temperature == 28.5
    assert weather.humidity == 85.0
    assert weather.precipitation == 12.0
    assert weather.rain == 8.0
    assert weather.showers == 4.0
    assert weather.wind_speed == 15.0
    assert weather.wind_gusts == 22.0
    assert weather.weather_code == 65
    assert len(weather.hourly_precipitation) == 2


@patch("services.weather_service.requests.get")
def test_fetch_live_weather_timeout(mock_get):
    # Mock timeout
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    with pytest.raises(WeatherAPIError):
        fetch_live_weather(19.0728, 72.8822)


@patch("services.weather_service.requests.get")
def test_fetch_live_weather_malformed_response(mock_get):
    # Mock empty or invalid response structure
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {} # missing current and hourly
    mock_get.return_value = mock_response

    with pytest.raises(WeatherAPIError):
        fetch_live_weather(19.0728, 72.8822)

import pytest
from models.data_models import UserProfile, WeatherData, EmergencyContact, RiskLevel
from services.risk_engine import calculate_risks

@pytest.fixture
def base_profile():
    return UserProfile(
        name="Test User",
        age=30,
        city="Mumbai",
        state="Maharashtra",
        latitude=19.0728,
        longitude=72.8822,
        lives_on_ground_floor=False,
        has_children=False,
        has_seniors=False,
        medical_conditions=[],
        has_vehicle=False,
        vehicle_type="None",
        daily_commute=False,
        commute_distance_km=0.0,
        preferred_language="English",
        emergency_contacts=[EmergencyContact(name="Contact", relation="Friend", phone="1234567890")],
        travel_today=False
    )

@pytest.fixture
def base_weather():
    return WeatherData(
        latitude=19.0728,
        longitude=72.8822,
        timezone="Asia/Kolkata",
        temperature=25.0,
        humidity=70.0,
        precipitation=0.0,
        rain=0.0,
        showers=0.0,
        wind_speed=10.0,
        wind_gusts=15.0,
        weather_code=0
    )


def test_risk_engine_no_rain_zero_risk(base_profile, base_weather):
    # No rain, no travel, standard adult, upper floor
    risks = calculate_risks(base_profile, base_weather, completed_checklists=0, total_checklists=0)
    
    assert risks.weather_severity_level == RiskLevel.LOW
    assert risks.flood_risk_level == RiskLevel.LOW
    assert risks.travel_risk_level == RiskLevel.LOW
    assert risks.health_risk_level == RiskLevel.LOW
    # Completed profile fields: name/city/state (+20), has contacts (+20) -> 40 points
    # No checklist items checked (completed=0, total=0 defaults to 60) -> overall 100%
    assert risks.overall_preparedness_score == 100


def test_risk_engine_heavy_rainfall_and_ground_floor(base_profile, base_weather):
    # Heavy rainfall (60mm) and ground floor dwelling
    base_profile.lives_on_ground_floor = True
    base_weather.rain = 40.0
    base_weather.showers = 20.0
    base_weather.weather_code = 65 # Heavy rain

    risks = calculate_risks(base_profile, base_weather, completed_checklists=2, total_checklists=6)
    
    assert risks.weather_severity_level in [RiskLevel.HIGH, RiskLevel.EXTREME]
    # Under heavy rain (60mm) and ground floor dwelling, flood risk must be High/Extreme
    assert risks.flood_risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]
    assert "ground floor" in risks.flood_risk_desc.lower()
    
    # 40 (profile) + 20 (checklist: 2/6 = 0.33 * 60) = 60
    assert risks.overall_preparedness_score == 60


def test_risk_engine_moderate_rainfall_apartment(base_profile, base_weather):
    # Moderate rain (8mm) and not ground floor
    base_weather.rain = 8.0
    base_weather.weather_code = 63 # Moderate rain

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.weather_severity_level == RiskLevel.MODERATE
    assert risks.flood_risk_level == RiskLevel.LOW


def test_risk_engine_senior_citizen_vulnerability(base_profile, base_weather):
    # Senior citizen in heavy rain -> elevated health risk
    base_profile.has_seniors = True
    base_weather.rain = 30.0
    base_weather.weather_code = 65

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.health_risk_level == RiskLevel.HIGH
    assert "senior" in risks.health_risk_desc.lower()


def test_risk_engine_child_vulnerability(base_profile, base_weather):
    # Child present in high rain -> elevated health risk
    base_profile.has_children = True
    base_weather.rain = 30.0
    base_weather.weather_code = 65

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.health_risk_level == RiskLevel.HIGH


def test_risk_engine_medical_condition_respiratory_trigger(base_profile, base_weather):
    # Asthma condition and high humidity -> high health risk
    base_profile.medical_conditions = ["Asthma"]
    base_weather.humidity = 88.0
    base_weather.weather_code = 61 # Light rain (moderate weather)

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.health_risk_level == RiskLevel.HIGH
    assert "asthma" in risks.health_risk_desc.lower()


def test_risk_engine_medical_condition_arthritis_trigger(base_profile, base_weather):
    # Arthritis, cold (15C) and damp (85% humidity) -> moderate health risk
    base_profile.medical_conditions = ["Arthritis"]
    base_weather.temperature = 15.0
    base_weather.humidity = 85.0
    base_weather.weather_code = 61

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.health_risk_level == RiskLevel.MODERATE
    assert "joint" in risks.health_risk_desc.lower()


def test_risk_engine_travel_two_wheeler_heavy_rain(base_profile, base_weather):
    # Planning to travel, 2-wheeler, heavy rain -> high travel risk
    base_profile.travel_today = True
    base_profile.vehicle_type = "2-Wheeler"
    base_weather.rain = 25.0
    base_weather.weather_code = 65

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.travel_risk_level == RiskLevel.HIGH
    assert "2-wheeler" in risks.travel_risk_desc.lower()


def test_risk_engine_travel_four_wheeler_heavy_rain(base_profile, base_weather):
    # Planning to travel, 4-wheeler, heavy rain -> moderate travel risk
    base_profile.travel_today = True
    base_profile.vehicle_type = "4-Wheeler"
    base_weather.rain = 25.0
    base_weather.weather_code = 65

    risks = calculate_risks(base_profile, base_weather)
    
    # Four-wheelers are safer, should return Moderate risk
    assert risks.travel_risk_level == RiskLevel.MODERATE


def test_risk_engine_multiple_risk_factors(base_profile, base_weather):
    # Ground floor resident, seniors in household, travel planned on a 2-wheeler, heavy storm
    base_profile.lives_on_ground_floor = True
    base_profile.has_seniors = True
    base_profile.travel_today = True
    base_profile.vehicle_type = "2-Wheeler"
    
    base_weather.rain = 45.0
    base_weather.wind_speed = 55.0
    base_weather.weather_code = 99 # Severe thunderstorm

    risks = calculate_risks(base_profile, base_weather)
    
    assert risks.weather_severity_level == RiskLevel.EXTREME
    assert risks.flood_risk_level == RiskLevel.EXTREME
    assert risks.travel_risk_level == RiskLevel.EXTREME
    assert risks.health_risk_level == RiskLevel.HIGH
    assert len(risks.risk_factors) >= 3

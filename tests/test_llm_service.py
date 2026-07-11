import pytest
from unittest.mock import patch, Mock
from models.data_models import UserProfile, WeatherData, RiskAssessment, EmergencyContact, RiskLevel
from services.llm_service import generate_preparedness_plan, generate_chat_response

@pytest.fixture
def mock_profile():
    return UserProfile(
        name="Sarah Connor",
        age=45,
        city="Los Angeles",
        state="California",
        latitude=34.0522,
        longitude=-118.2437,
        lives_on_ground_floor=True,
        has_children=False,
        has_seniors=False,
        medical_conditions=["Asthma"],
        has_vehicle=True,
        vehicle_type="4-Wheeler",
        daily_commute=True,
        commute_distance_km=25.0,
        preferred_language="English",
        emergency_contacts=[EmergencyContact(name="John", relation="Son", phone="9999999999")],
        travel_today=True
    )

@pytest.fixture
def mock_weather():
    return WeatherData(
        latitude=34.0522,
        longitude=-118.2437,
        timezone="America/Los_Angeles",
        temperature=18.0,
        humidity=92.0,
        precipitation=35.0,
        rain=20.0,
        showers=15.0,
        wind_speed=45.0,
        wind_gusts=60.0,
        weather_code=65
    )

@pytest.fixture
def mock_risks():
    return RiskAssessment(
        flood_risk_level=RiskLevel.HIGH,
        flood_risk_desc="High risk of localized flash flooding.",
        travel_risk_level=RiskLevel.MODERATE,
        travel_risk_desc="Drive with caution due to heavy rain and winds.",
        health_risk_level=RiskLevel.HIGH,
        health_risk_desc="High humidity triggers asthma warning.",
        weather_severity_level=RiskLevel.HIGH,
        weather_severity_desc="High severity storm active.",
        overall_preparedness_score=80,
        risk_factors=["Heavy rain", "Asthma presence"]
    )


@patch("services.llm_service.get_gemini_client")
def test_llm_plan_prompt_construction(mock_get_client, mock_profile, mock_weather, mock_risks):
    # Mock Gemini Client generate_content call
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = "Here is your plan. Take shelter."
    mock_client.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_client

    plan = generate_preparedness_plan(mock_profile, mock_weather, mock_risks)
    
    assert plan == "Here is your plan. Take shelter."
    
    # Extract arguments passed to client.models.generate_content
    called_args = mock_client.models.generate_content.call_args[1]
    prompt_used = called_args["contents"]
    config_used = called_args["config"]

    # Verify structured JSON-like elements and variables are in prompt
    assert "Sarah Connor" in prompt_used
    assert "Los Angeles" in prompt_used
    assert "Asthma" in prompt_used
    assert "35.0 mm" in prompt_used
    assert "80/100" in prompt_used
    
    # Assert system instruction acts as hallucination guard
    system_instr = config_used.system_instruction
    assert "Only answer using the supplied structured context" in system_instr
    assert "Never invent" in system_instr


@patch("services.llm_service.get_gemini_client")
def test_llm_chat_prompt_construction(mock_get_client, mock_profile, mock_weather, mock_risks):
    # Mock chat response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = "You should stay indoors due to the high flood risk."
    mock_client.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_client

    history = [{"role": "user", "content": "Can I travel to work?"}]
    response = generate_chat_response(mock_profile, mock_weather, mock_risks, history, "Should I go?")
    
    assert response == "You should stay indoors due to the high flood risk."
    
    # Extract prompt used
    prompt_used = mock_client.models.generate_content.call_args[1]["contents"]
    config_used = mock_client.models.generate_content.call_args[1]["config"]

    # Assert structured context is present
    assert "Sarah Connor" in prompt_used
    assert "Can I travel to work?" in prompt_used
    assert "Should I go?" in prompt_used
    
    # Check system instruction hallucination guard
    system_instr = config_used.system_instruction
    assert "Only answer using the supplied" in system_instr
    assert "Never hallucinate" in system_instr


@patch("services.llm_service.get_gemini_client")
def test_llm_api_exception_handling(mock_get_client, mock_profile, mock_weather, mock_risks):
    # Simulate API connection error
    mock_client = Mock()
    mock_client.models.generate_content.side_effect = Exception("Google API Quota Exceeded")
    mock_get_client.return_value = mock_client

    response = generate_preparedness_plan(mock_profile, mock_weather, mock_risks)
    assert "Unable to generate plan due to API issue: Google API Quota Exceeded" in response

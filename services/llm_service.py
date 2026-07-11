import os
import streamlit as st
import html
import re
from typing import Optional
from google import genai
from google.genai import types
from models.data_models import UserProfile, WeatherData, RiskAssessment

def get_gemini_client() -> genai.Client:
    """
    Retrieves the Gemini SDK client.
    Extracts API key from Streamlit secrets or environment variables.
    """
    api_key = None
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        elif "gemini_api_key" in st.secrets:
            api_key = st.secrets["gemini_api_key"]
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Please set the GEMINI_API_KEY environment variable "
            "or configure it in Streamlit Secrets."
        )
    return genai.Client(api_key=api_key)

def sanitize_user_input(text: str) -> str:
    """
    Cleans user input to prevent prompt injection and XSS tags.
    """
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]*>", "", text)
    # Escape any HTML special characters
    return html.escape(clean.strip())

def generate_preparedness_plan(profile: UserProfile, weather: WeatherData, risks: RiskAssessment) -> str:
    """
    Generates a natural language weather preparedness plan based strictly on structured context.
    """
    try:
        client = get_gemini_client()
    except ValueError as e:
        return f"**LLM Service Error**: {e}"

    system_instruction = (
        "Only answer using the supplied structured context. Never invent weather details, "
        "flood warnings, emergency alerts, road closures, or medical advice. If information "
        "is unavailable, state that clearly and do not guess. Focus on giving action-oriented "
        "preparedness tips directly matching the profile risks."
    )

    prompt = f"""
    You are the Guardian360 Preparedness Planner. Generate a clear, bulleted preparedness plan based strictly on this structured data:
    
    [PROFILE]
    Name: {profile.name}
    Age: {profile.age}
    Location: {profile.city}, {profile.state}
    Family Context: Children: {profile.has_children}, Seniors: {profile.has_seniors}
    Medical Issues: {", ".join(profile.medical_conditions) if profile.medical_conditions else "None"}
    Dwelling: {"Ground Floor (High risk of water entry)" if profile.lives_on_ground_floor else "Above Ground Floor"}
    Vehicle type: {profile.vehicle_type}
    Transit: Commuting distance: {profile.commute_distance_km} km. Travel planned today: {profile.travel_today}
    Language: {profile.preferred_language}

    [LIVE WEATHER]
    Current Temperature: {weather.temperature}°C
    Relative Humidity: {weather.humidity}%
    Current Rainfall/Showers: {weather.precipitation} mm
    Wind Speed: {weather.wind_speed} km/h (Gusts: {weather.wind_gusts} km/h)
    WMO Weather Code: {weather.weather_code}

    [DETERMINISTIC RISKS]
    Weather Severity: {risks.weather_severity_level.value} - {risks.weather_severity_desc}
    Flood Risk: {risks.flood_risk_level.value} - {risks.flood_risk_desc}
    Travel Risk: {risks.travel_risk_level.value} - {risks.travel_risk_desc}
    Health Risk: {risks.health_risk_level.value} - {risks.health_risk_desc}
    Overall Preparedness Score: {risks.overall_preparedness_score}/100

    Please generate a cohesive document detailing:
    1. Today's preparation instructions.
    2. Things to carry if commuting.
    3. Activities/areas to avoid.
    4. Vehicle safety precautions.
    5. Household/Family precautions.
    6. Health precautions tailored to listed conditions.
    7. Emergency contacts reminder (Inform the user to refer to contacts list).

    *Rules*:
    - Only use the structured data provided below.
    - Never invent weather information.
    - Never create warnings not present in the supplied data.
    - If information is unavailable, clearly state that it is unavailable.
    - Generate the response in the user's preferred language ({profile.preferred_language}).
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        return response.text if response.text else "Failed to generate plan contents."
    except Exception as e:
        return f"Unable to generate plan due to API issue: {e}"

def extract_city_from_message(message: str) -> Optional[str]:
    """
    Extracts a city name from the query.
    Uses a fast lookup dict first, then queries Gemini NLP extractor.
    """
    words = [w.strip(",.?!()\"'") for w in message.split()]
    common_cities = {
        "lonavala": "Lonavla",
        "lonavla": "Lonavla",
        "mumbai": "Mumbai",
        "pune": "Pune",
        "bengaluru": "Bangalore",
        "bangalore": "Bangalore",
        "delhi": "Delhi",
        "kolkata": "Kolkata",
        "chennai": "Chennai"
    }
    for w in words:
        wl = w.lower()
        if wl in common_cities:
            return common_cities[wl]

    try:
        client = get_gemini_client()
        prompt = f"Identify and extract the single city name mentioned in this sentence: '{message}'. If no city is mentioned, reply strictly with the word 'None'."
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        result = response.text.strip().replace("'", "").replace('"', "").strip()
        if result.lower() == "none" or len(result) < 2 or " " in result or len(result) > 30:
            return None
        return result
    except Exception:
        return None

def generate_chat_response(profile: UserProfile, weather: WeatherData, risks: RiskAssessment, chat_history: list, new_message: str) -> str:
    """
    Answers a conversational question from the user based strictly on the current weather and risk context.
    If the user mentions another city, we dynamically fetch coordinates, weather, and risks for that location.
    """
    from typing import Optional
    
    try:
        client = get_gemini_client()
    except ValueError as e:
        return f"**LLM Service Error**: {e}"

    sanitized_message = sanitize_user_input(new_message)
    if not sanitized_message:
        return "I received an empty message or invalid characters. Please try asking another question."

    # Try to extract the target city name
    target_city = extract_city_from_message(sanitized_message)
    target_weather = None
    target_risks = None

    if target_city and target_city.lower() != profile.city.lower():
        from services.weather_service import get_coordinates, fetch_live_weather
        from services.risk_engine import calculate_risks as run_risk_engine
        try:
            lat, lon, res_city, res_state, country = get_coordinates(target_city)
            target_weather = fetch_live_weather(lat, lon)
            
            # Clone profile for target city transit evaluations
            cloned_profile = profile.model_copy()
            cloned_profile.city = res_city
            cloned_profile.state = res_state
            cloned_profile.latitude = lat
            cloned_profile.longitude = lon
            
            target_risks = run_risk_engine(cloned_profile, target_weather)
        except Exception:
            pass

    system_instruction = (
        "Only answer using the supplied structured context. You are the Guardian360 Climate Assistant. "
        "Answer the user's questions strictly using the provided profile, weather parameters, and risk values. "
        "Never hallucinate. Never invent road closures, local flood levels, or medical cures. If a question "
        "is not answerable using the provided data, politely tell the user you do not have that real-time "
        "information and advise them to consult local authorities."
    )

    context_str = f"""
    [PROFILE CITY CONTEXT]
    User: {profile.name} (Age: {profile.age})
    Onboarded City: {profile.city}, {profile.state} (lat: {profile.latitude:.4f}, lon: {profile.longitude:.4f})
    Current Weather: Temp {weather.temperature}°C, Humidity {weather.humidity}%, Rain {weather.precipitation} mm, Wind {weather.wind_speed} km/h
    Calculated Risks: Flood ({risks.flood_risk_level.value}), Travel ({risks.travel_risk_level.value}), Health ({risks.health_risk_level.value}), Weather Severity ({risks.weather_severity_level.value})
    """

    if target_weather and target_risks:
        context_str += f"""
        [REQUESTED TARGET CITY CONTEXT]
        Target Location: {target_city} (lat: {target_weather.latitude:.4f}, lon: {target_weather.longitude:.4f})
        Current Weather: Temp {target_weather.temperature}°C, Humidity {target_weather.humidity}%, Rain {target_weather.precipitation} mm, Wind {target_weather.wind_speed} km/h
        Calculated Risks: Flood ({target_risks.flood_risk_level.value}), Travel ({target_risks.travel_risk_level.value}), Health ({target_risks.health_risk_level.value}), Weather Severity ({target_risks.weather_severity_level.value})
        """

    history_block = ""
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        history_block += f"{role}: {content}\n"

    prompt = f"""
    {context_str}

    [CONVERSATION HISTORY]
    {history_block}
    User Query: {sanitized_message}

    Please reply in the preferred language ({profile.preferred_language}). Remember, only answer using the supplied context. Do not invent details.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        return response.text if response.text else "Sorry, I could not generate a response."
    except Exception as e:
        return f"Error executing assistant query: {e}"

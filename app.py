import streamlit as st
import os
import json
import pandas as pd
import html
import re
from typing import Optional
from dotenv import load_dotenv

# Load local environment files if present
load_dotenv()

# Set page configuration first
st.set_page_config(
    page_title="Guardian360 - Climate Preparedness Platform",
    page_icon="⛈️ ",
    layout="wide",
    initial_sidebar_state="expanded"
)

from models.data_models import UserProfile, WeatherData, RiskAssessment, EmergencyContact, RiskLevel
from services.weather_service import get_coordinates, fetch_live_weather, LocationNotFoundError, WeatherAPIError
from services.risk_engine import calculate_risks
from services.llm_service import generate_preparedness_plan, generate_chat_response, sanitize_user_input
from services.checklist_service import get_standard_checklist, get_travel_checklist, get_emergency_checklist, get_offline_tips
from utils.helpers import sanitize_html, generate_preparedness_pdf, get_custom_css

# --- Profile Persistence ---
PROFILE_FILE = "user_profile.json"

def save_profile_locally(profile: UserProfile):
    """Saves user profile model to local JSON file for session persistence."""
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            f.write(profile.model_dump_json())
    except Exception as e:
        st.error(f"Security/IO Error: Unable to save profile locally: {e}")

def load_profile_locally() -> Optional[UserProfile]:
    """Loads user profile from local JSON file if exists."""
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return UserProfile(**data)
        except Exception:
            # Corrupted file or invalid schema: return None to allow re-onboarding
            return None
    return None

# --- Session State Initialization ---
if "profile" not in st.session_state:
    st.session_state.profile = load_profile_locally()

if "weather" not in st.session_state:
    st.session_state.weather = None

if "risks" not in st.session_state:
    st.session_state.risks = None

if "preparedness_plan" not in st.session_state:
    st.session_state.preparedness_plan = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "checklist_status" not in st.session_state:
    st.session_state.checklist_status = {}

if "manual_emergency_override" not in st.session_state:
    st.session_state.manual_emergency_override = False

# --- CSS Theme Injection ---
# Determine if Emergency Mode is active:
# Triggered if weather severity is High/Extreme OR if user overrides manually
is_emergency = st.session_state.manual_emergency_override
if st.session_state.risks:
    level = st.session_state.risks.weather_severity_level
    if level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
        is_emergency = True

st.markdown(get_custom_css(emergency_mode=is_emergency), unsafe_allow_html=True)

# --- Sidebar / Navigation Router ---
st.sidebar.markdown("<h2 class='accent-header'>⛈️ Guardian360</h2>", unsafe_allow_html=True)
st.sidebar.markdown("*AI-Powered Climate Preparedness*")
st.sidebar.markdown("---")

# Visual warning banner if emergency mode is active
if is_emergency:
    st.sidebar.markdown(
        "<div class='emergency-banner'>⚠️ EMERGENCY MODE ACTIVE</div>",
        unsafe_allow_html=True
    )

# Step selections
nav_options = [
    "1. Welcome & Introduction",
    "2. Onboarding & Profile",
    "3. Live Weather & Risks",
    "4. AI Preparedness Planner",
    "5. Chat Assistant",
    "6. Emergency Response Portal",
    "7. Export Summary Report"
]

selected_step = st.sidebar.radio(
    "Navigation Steps", 
    nav_options, 
    index=0,
    help="Select a stage of your climate preparedness journey."
)

st.sidebar.markdown(
    "<div class='footer-text'>Guardian360 Platform &copy; 2026<br>Preparedness & Safety First</div>", 
    unsafe_allow_html=True
)

# --- STEP 1: Landing Page ---
if selected_step == "1. Welcome & Introduction":
    st.markdown("<h1 class='accent-header'>Guardian360</h1>", unsafe_allow_html=True)
    st.markdown("### Prepare for the Monsoon Season with Confidence")
    
    st.markdown(
        """
        <div class='glass-card'>
            <h4>About the Platform</h4>
            <p>Monsoons can bring sudden weather transitions, flooding, transit hazards, and health concerns. 
            Guardian360 guides families through a step-by-step preparedness journey by analyzing live weather data and calculating local risks.</p>
            <p><strong>Your safety recommendations are tailored to:</strong></p>
            <ul>
                <li><strong>Current Local Weather:</strong> Fetched in real-time from open-source APIs.</li>
                <li><strong>Dwelling Profile:</strong> Risks are evaluated differently if you reside on the ground floor.</li>
                <li><strong>Family Vulnerabilities:</strong> Specific precautions are issued if seniors or children live with you.</li>
                <li><strong>Health Factors:</strong> Real-time atmospheric conditions alert those with respiratory or joint conditions.</li>
                <li><strong>Transit Plans:</strong> Commuting risk calculations adapt to your vehicle type (e.g. 2-wheeler vs 4-wheeler).</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class='glass-card'>
                <h5>🧠 Hallucination-Resistant AI</h5>
                <p>Guardian360 uses a hybrid architecture. Risk calculations and safety decisions are handled 
                by <strong>deterministic Python logic</strong>, never by LLM guesses. Gemini 2.5 Flash is restricted to explaining 
                these results with strict context constraints.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div class='glass-card'>
                <h5>📴 Offline Resilience</h5>
                <p>In cases of extreme weather, the system initiates <strong>Emergency Mode</strong> automatically, 
                reorienting the UI to highlight offline survival tip cards, emergency numbers, and key checklists.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    if st.button("Start Your Preparedness Journey ➡️"):
        st.info("Please navigate to Step 2 in the sidebar to configure your profile.")

# --- STEP 2: Onboarding & Profile ---
elif selected_step == "2. Onboarding & Profile":
    st.markdown("<h1 class='accent-header'>User Profile Onboarding</h1>", unsafe_allow_html=True)
    st.write("Complete the profile setup to enable localized hazard risk modeling.")
    
    # Check if a profile is already stored
    profile = st.session_state.profile
    
    with st.form("onboarding_form"):
        st.markdown("<h5>1. Identity & Location</h5>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            name_val = st.text_input("Full Name", value=profile.name if profile else "", placeholder="e.g. Sarah Smith")
            age_val = st.number_input("Age", min_value=0, max_value=120, value=profile.age if profile else 30)
        with col2:
            city_val = st.text_input("City", value=profile.city if profile else "", placeholder="e.g. Mumbai")
            state_val = st.text_input("State", value=profile.state if profile else "", placeholder="e.g. Maharashtra")
            
        st.markdown("<h5>2. Household & Health Context</h5>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            ground_floor_val = st.checkbox("Reside on Ground Floor", value=profile.lives_on_ground_floor if profile else False)
            seniors_val = st.checkbox("Living with Senior Citizens", value=profile.has_seniors if profile else False)
            children_val = st.checkbox("Living with Children (Under 5 years old)", value=profile.has_children if profile else False)
        with col4:
            med_list = ["Asthma/COPD", "Arthritis/Joint Pain", "Heart Disease", "Diabetes"]
            default_meds = []
            if profile:
                # Map stored strings to options
                default_meds = [m for m in med_list if any(x in m for x in profile.medical_conditions)]
            med_val = st.multiselect("Medical Conditions in Household", options=med_list, default=default_meds)

        st.markdown("<h5>3. Transit & Commute Setup</h5>", unsafe_allow_html=True)
        col5, col6 = st.columns(2)
        with col5:
            travel_today_val = st.checkbox("Planning to travel/commute today?", value=profile.travel_today if profile else False)
            has_vehicle_val = st.checkbox("Own a personal vehicle", value=profile.has_vehicle if profile else False)
        with col6:
            vehicle_type_val = st.selectbox("Vehicle Type", options=["None", "2-Wheeler", "4-Wheeler"], index=["None", "2-Wheeler", "4-Wheeler"].index(profile.vehicle_type if profile else "None"))
            commute_dist_val = st.number_input("Daily Commute Distance (km)", min_value=0.0, max_value=500.0, value=profile.commute_distance_km if profile else 0.0)

        st.markdown("<h5>4. Preferences & Emergency</h5>", unsafe_allow_html=True)
        col7, col8 = st.columns(2)
        with col7:
            lang_val = st.selectbox("Preferred Language", options=["English", "Hindi", "Marathi", "Spanish"], index=["English", "Hindi", "Marathi", "Spanish"].index(profile.preferred_language if profile else "English"))
        with col8:
            st.markdown("*Emergency Contact:*")
            contact_name = st.text_input("Contact Name", value=profile.emergency_contacts[0].name if profile and profile.emergency_contacts else "", placeholder="e.g. John Doe")
            contact_rel = st.text_input("Relationship", value=profile.emergency_contacts[0].relation if profile and profile.emergency_contacts else "", placeholder="e.g. Spouse")
            contact_phone = st.text_input("Phone Number", value=profile.emergency_contacts[0].phone if profile and profile.emergency_contacts else "", placeholder="e.g. +919876543210")

        submitted = st.form_submit_button("Save Profile Details")
        
        if submitted:
            # Inputs validation
            if not name_val.strip() or len(name_val.strip()) < 2:
                st.error("Validation Error: Please enter a valid name (at least 2 characters).")
            elif not city_val.strip() or len(city_val.strip()) < 2:
                st.error("Validation Error: Please enter a valid city name.")
            elif not state_val.strip() or len(state_val.strip()) < 2:
                st.error("Validation Error: Please enter a valid state name.")
            elif not contact_name.strip() or not contact_phone.strip() or not contact_rel.strip():
                st.error("Validation Error: Emergency contact details are mandatory.")
            elif not re.match(r"^\+?[0-9]{7,15}$", contact_phone.strip().replace(" ", "").replace("-", "")):
                st.error("Validation Error: Please enter a valid phone number (7 to 15 digits).")
            else:
                # Format medical conditions list
                mapped_meds = []
                for m in med_val:
                    if "Asthma" in m: mapped_meds.append("Asthma")
                    elif "Arthritis" in m: mapped_meds.append("Arthritis")
                    elif "Heart" in m: mapped_meds.append("Heart Disease")
                    elif "Diabetes" in m: mapped_meds.append("Diabetes")
                
                # Fetch Coordinates using Weather geocoding
                try:
                    with st.spinner("Resolving coordinates for city..."):
                        lat, lon, res_city, res_state, country = get_coordinates(city_val, state_val)
                    
                    contacts = [EmergencyContact(name=sanitize_html(contact_name), relation=sanitize_html(contact_rel), phone=sanitize_html(contact_phone))]
                    
                    # Create profile object
                    profile_obj = UserProfile(
                        name=sanitize_html(name_val),
                        age=age_val,
                        city=sanitize_html(res_city),
                        state=sanitize_html(res_state),
                        latitude=lat,
                        longitude=lon,
                        lives_on_ground_floor=ground_floor_val,
                        has_children=children_val,
                        has_seniors=seniors_val,
                        medical_conditions=mapped_meds,
                        has_vehicle=has_vehicle_val,
                        vehicle_type=vehicle_type_val if has_vehicle_val else "None",
                        daily_commute=travel_today_val,
                        commute_distance_km=commute_dist_val,
                        preferred_language=lang_val,
                        emergency_contacts=contacts,
                        travel_today=travel_today_val
                    )
                    
                    st.session_state.profile = profile_obj
                    save_profile_locally(profile_obj)
                    
                    # Flush weather caches and reset plan to force refresh
                    st.session_state.weather = None
                    st.session_state.risks = None
                    st.session_state.preparedness_plan = ""
                    
                    st.success(f"Profile saved successfully! Coordinates resolved: {lat:.4f}, {lon:.4f} ({res_city}, {res_state})")
                    st.balloons()
                except LocationNotFoundError as le:
                    st.error(f"Geocoding Error: {le}")
                except WeatherAPIError as we:
                    st.error(f"Weather Service Unavailable: {we}")

# --- Lock Validation for Steps 3-7 ---
else:
    if st.session_state.profile is None:
        st.markdown("<h1 class='accent-header'>Guardian360</h1>", unsafe_allow_html=True)
        st.warning("⚠️ Access Locked: Please complete the Onboarding & Profile Setup (Step 2) to continue.")
        st.info("We require your location and profile variables to compute risk assessments and fetch current weather data.")
    
    else:
        profile = st.session_state.profile
        
        # --- Fetch Weather & Risk engine on the fly if not cached ---
        if st.session_state.weather is None:
            try:
                with st.spinner("Fetching live weather and analyzing climate risks..."):
                    weather_obj = fetch_live_weather(profile.latitude, profile.longitude)
                    st.session_state.weather = weather_obj
            except WeatherAPIError as e:
                st.error(f"Weather API Error: {e}")
        
        # Compute risks if weather is resolved
        if st.session_state.weather and st.session_state.risks is None:
            # Pre-initialize checklist map if empty
            std_chk = get_standard_checklist()
            trv_chk = get_travel_checklist() if profile.travel_today else []
            combined_items = std_chk + trv_chk
            
            for item in combined_items:
                if item not in st.session_state.checklist_status:
                    st.session_state.checklist_status[item] = False
            
            completed = sum(1 for val in st.session_state.checklist_status.values() if val)
            total = len(st.session_state.checklist_status)
            
            st.session_state.risks = calculate_risks(profile, st.session_state.weather, completed, total)

        # Proceed only if we have active data
        if st.session_state.weather and st.session_state.risks:
            weather = st.session_state.weather
            risks = st.session_state.risks

            # --- STEP 3: Live Weather & Risks ---
            if selected_step == "3. Live Weather & Risks":
                st.markdown(f"<h1 class='accent-header'>Weather & Preparedness Dashboard</h1>", unsafe_allow_html=True)
                st.write(f"Showing live updates for: **{profile.city}, {profile.state}** (lat: {profile.latitude:.4f}, lon: {profile.longitude:.4f})")
                
                # Current Weather Cards
                st.subheader("Current Weather Observations")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <p style='font-size: 0.9em; margin-bottom: 2px; color: #94a3b8;'>Temperature</p>
                            <h2 style='margin: 0; color: #38bdf8;'>{weather.temperature:.1f} °C</h2>
                            <p style='font-size: 0.8em; color: #64748b;'>WMO Weather Code: {weather.weather_code}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <p style='font-size: 0.9em; margin-bottom: 2px; color: #94a3b8;'>Humidity</p>
                            <h2 style='margin: 0; color: #38bdf8;'>{weather.humidity:.1f} %</h2>
                            <p style='font-size: 0.8em; color: #64748b;'>Atmospheric density</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col3:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <p style='font-size: 0.9em; margin-bottom: 2px; color: #94a3b8;'>Current Rainfall</p>
                            <h2 style='margin: 0; color: #38bdf8;'>{weather.precipitation:.1f} mm</h2>
                            <p style='font-size: 0.8em; color: #64748b;'>Rain: {weather.rain:.1f}mm | Showers: {weather.showers:.1f}mm</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col4:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <p style='font-size: 0.9em; margin-bottom: 2px; color: #94a3b8;'>Wind Speed</p>
                            <h2 style='margin: 0; color: #38bdf8;'>{weather.wind_speed:.1f} km/h</h2>
                            <p style='font-size: 0.8em; color: #64748b;'>Wind Gusts: {weather.wind_gusts:.1f} km/h</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Hourly Precipitation Forecast chart
                if weather.hourly_time and weather.hourly_precipitation:
                    st.subheader("24-Hour Precipitation & Temperature Trend")
                    hourly_df = pd.DataFrame({
                        "Time": pd.to_datetime(weather.hourly_time[:24]).strftime("%H:%M"),
                        "Rainfall (mm)": weather.hourly_precipitation[:24],
                        "Temp (°C)": weather.hourly_temperature[:24]
                    })
                    st.line_chart(hourly_df, x="Time", y=["Rainfall (mm)", "Temp (°C)"])

                st.markdown("---")
                
                # Deterministic Risks Output
                st.subheader("Rule-Based Safety Assessment Indicators")
                
                def get_badge_html(level: RiskLevel) -> str:
                    if level == RiskLevel.LOW:
                        return "<span class='risk-badge-low'>🟢 Low Risk</span>"
                    elif level == RiskLevel.MODERATE:
                        return "<span class='risk-badge-moderate'>🟡 Moderate Risk</span>"
                    elif level == RiskLevel.HIGH:
                        return "<span class='risk-badge-high'>🔴 High Risk</span>"
                    else:
                        return "<span class='risk-badge-extreme'>🚨 EXTREME RISK</span>"

                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <strong>🌧️ Flood Exposure Risk</strong>
                                {get_badge_html(risks.flood_risk_level)}
                            </div>
                            <p style='margin-top: 10px; font-size: 0.95em;'>{risks.flood_risk_desc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <strong>🚗 Travel Safety Risk</strong>
                                {get_badge_html(risks.travel_risk_level)}
                            </div>
                            <p style='margin-top: 10px; font-size: 0.95em;'>{risks.travel_risk_desc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with rc2:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <strong>⚕️ Health & Vulnerability Risk</strong>
                                {get_badge_html(risks.health_risk_level)}
                            </div>
                            <p style='margin-top: 10px; font-size: 0.95em;'>{risks.health_risk_desc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <strong>🌪️ Weather Severity Rating</strong>
                                {get_badge_html(risks.weather_severity_level)}
                            </div>
                            <p style='margin-top: 10px; font-size: 0.95em;'>{risks.weather_severity_desc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Overall Preparedness Score and Interactive checklist
                st.markdown("---")
                st.subheader("Interactive Preparedness Tracker")
                
                col_score, col_chk = st.columns([1, 2])
                with col_score:
                    # Circular score or large text block
                    color = "#10b981" # Green
                    if risks.overall_preparedness_score < 40:
                        color = "#ef4444" # Red
                    elif risks.overall_preparedness_score < 75:
                        color = "#f59e0b" # Orange
                        
                    st.markdown(
                        f"""
                        <div class='glass-card' style='text-align: center; height: 100%;'>
                            <h4>Current Preparedness</h4>
                            <h1 style='font-size: 4em; color: {color}; margin: 15px 0;'>{risks.overall_preparedness_score}%</h1>
                            <p style='font-size: 0.85em; color: #94a3b8;'>Complete your profile info and check off items in the checklist to increase your score.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                with col_chk:
                    st.write("Complete the checks below to secure your home and travel path:")
                    
                    # Create checklist checkmarks in streamlit and capture change
                    std_list = get_standard_checklist()
                    trv_list = get_travel_checklist() if profile.travel_today else []
                    
                    changed = False
                    
                    st.markdown("##### Standard House & Supply Checklists:")
                    for item in std_list:
                        checked_val = st.checkbox(item, value=st.session_state.checklist_status.get(item, False), key=f"std_{item}")
                        if checked_val != st.session_state.checklist_status.get(item, False):
                            st.session_state.checklist_status[item] = checked_val
                            changed = True
                            
                    if trv_list:
                        st.markdown("##### Planned Commute Safety Checklists:")
                        for item in trv_list:
                            checked_val = st.checkbox(item, value=st.session_state.checklist_status.get(item, False), key=f"trv_{item}")
                            if checked_val != st.session_state.checklist_status.get(item, False):
                                st.session_state.checklist_status[item] = checked_val
                                changed = True
                                
                    if changed:
                        # Re-calculate overall score dynamically and refresh state
                        completed = sum(1 for val in st.session_state.checklist_status.values() if val)
                        total = len(st.session_state.checklist_status)
                        st.session_state.risks = calculate_risks(profile, weather, completed, total)
                        st.rerun()

            # --- STEP 4: AI Preparedness Planner ---
            elif selected_step == "4. AI Preparedness Planner":
                st.markdown("<h1 class='accent-header'>AI Action Planner</h1>", unsafe_allow_html=True)
                st.write("This section passes structured JSON contexts directly to Gemini 2.5 Flash to write customized safety recommendations. No weather coordinates or severity levels are invented.")
                
                # Checkbox to refresh plan
                if st.button("Generate/Refresh AI Preparedness Plan ⚡") or not st.session_state.preparedness_plan:
                    with st.spinner("Gemini is formatting your personalized safety plan..."):
                        plan = generate_preparedness_plan(profile, weather, risks)
                        st.session_state.preparedness_plan = plan
                        
                if st.session_state.preparedness_plan:
                    st.markdown(
                        f"""
                        <div class='glass-card'>
                            <h4>Personalized Preparedness Protocol</h4>
                            <div style='margin-top: 15px;'>
                                {st.session_state.preparedness_plan}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("Click the button above to execute the GenAI Planner service.")

            # --- STEP 5: Chat Assistant ---
            elif selected_step == "5. Chat Assistant":
                st.markdown("<h1 class='accent-header'>Interactive AI Companion</h1>", unsafe_allow_html=True)
                st.write("Ask natural language safety questions. The assistant is anchored strictly to your live profile weather context and does not guess.")
                
                st.markdown("💡 *Suggested questions: Click to ask*")
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                
                clicked_prompt = None
                with col_s1:
                    if st.button("🚗 Can I travel safely today?", key="sq_1"):
                        clicked_prompt = "Can I travel safely in my city today?"
                with col_s2:
                    if st.button("👵 Precautions for family?", key="sq_2"):
                        clicked_prompt = "What safety precautions should I take for my family members today?"
                with col_s3:
                    if st.button("🫁 Asthma health alerts?", key="sq_3"):
                        clicked_prompt = "Are there any health triggers or precautions for cardiorespiratory/asthma conditions today?"
                with col_s4:
                    if st.button("⛈️ Can I commute to Lonavla?", key="sq_4"):
                        clicked_prompt = "Can I commute to Lonavla safely today?"

                # Display Chat Messages
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Chat input
                prompt = st.chat_input("Ask a safety question...")
                if clicked_prompt:
                    prompt = clicked_prompt

                if prompt:
                    # Render user input
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    
                    # Generate response
                    with st.spinner("AI Assistant is thinking..."):
                        response = generate_chat_response(profile, weather, risks, st.session_state.chat_history[:-1], prompt)
                        
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    if clicked_prompt:
                        st.rerun()

            # --- STEP 6: Emergency Response Portal ---
            elif selected_step == "6. Emergency Response Portal":
                st.markdown("<h1 class='accent-header'>Emergency Portal</h1>", unsafe_allow_html=True)
                
                # If emergency is manually forced but weather severity is normal, explain it
                if not (risks.weather_severity_level in [RiskLevel.HIGH, RiskLevel.EXTREME]) and st.session_state.manual_emergency_override:
                    st.warning("⚠️ Manual Override: Emergency mode is manually active. High-risk warning systems loaded.")
                    
                st.markdown(
                    """
                    <div class='emergency-banner'>
                        🚨 CRITICAL DISASTER RESPONSE INTERFACE ACTIVE
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(
                        """
                        <div class='glass-card'>
                            <h4>🚨 Critical Safety Evacuation Checklist</h4>
                            <p style='color: #fee2e2; font-size: 0.9em; margin-bottom: 15px;'>Take these actions immediately to preserve life and safety during storm incidents:</p>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Emergency checklist
                    em_chk = get_emergency_checklist()
                    for idx, item in enumerate(em_chk):
                        st.markdown(f"**{idx+1}.** {item}")
                        
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown(
                        """
                        <div class='glass-card'>
                            <h4>📞 Emergency Numbers Directory</h4>
                            <ul>
                                <li><strong>National Disaster Management (NDMA):</strong> 1078</li>
                                <li><strong>Police Assistance:</strong> 112 / 100</li>
                                <li><strong>Fire & Safety Services:</strong> 101</li>
                                <li><strong>Ambulance Emergency:</strong> 102</li>
                                <li><strong>Monsoon Control Hotline:</strong> 1916 (Municipal)</li>
                            </ul>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                with col2:
                    st.markdown(
                        """
                        <div class='glass-card'>
                            <h4>📴 Offline Resilience Tips</h4>
                            <p style='font-size: 0.9em; margin-bottom: 15px;'>In case of network tower failures or power blackouts, recall these actions:</p>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    offline_tips = get_offline_tips()
                    for tip in offline_tips:
                        st.markdown(f"🚩 **{tip['title']}:**")
                        st.markdown(f"*{tip['tip']}*")
                        st.markdown("---")
                        
                    st.markdown("</div>", unsafe_allow_html=True)

            # --- STEP 7: Export Summary Report ---
            elif selected_step == "7. Export Summary Report":
                st.markdown("<h1 class='accent-header'>Preparedness Summary Export</h1>", unsafe_allow_html=True)
                st.write("Export your calculated risk metrics, local live weather data, and AI action plan to a portable PDF report.")
                
                st.markdown(
                    f"""
                    <div class='glass-card'>
                        <h4>Preparedness Overview for {profile.name}</h4>
                        <ul>
                            <li><strong>Location:</strong> {profile.city}, {profile.state}</li>
                            <li><strong>Calculated Flood Risk:</strong> {risks.flood_risk_level.value}</li>
                            <li><strong>Calculated Commuting Risk:</strong> {risks.travel_risk_level.value}</li>
                            <li><strong>Overall Preparedness Score:</strong> {risks.overall_preparedness_score}%</li>
                        </ul>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Check if plan has been generated
                if not st.session_state.preparedness_plan:
                    st.warning("⚠️ Preparedness plan has not been generated yet. Please visit Step 4: AI Preparedness Planner first, or generate it below.")
                    if st.button("Generate Preparedness Plan Now"):
                        with st.spinner("Generating..."):
                            st.session_state.preparedness_plan = generate_preparedness_plan(profile, weather, risks)
                            st.rerun()
                
                if st.session_state.preparedness_plan:
                    # Export button
                    try:
                        pdf_data = generate_preparedness_pdf(
                            profile, 
                            weather, 
                            risks, 
                            st.session_state.preparedness_plan
                        )
                        
                        st.download_button(
                            label="📥 Download Personalized PDF Report",
                            data=pdf_data,
                            file_name=f"Guardian360_Report_{profile.city}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Error compiling PDF: {e}")

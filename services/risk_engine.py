from models.data_models import UserProfile, WeatherData, RiskAssessment, RiskLevel
from typing import List

def calculate_risks(profile: UserProfile, weather: WeatherData, completed_checklists: int = 0, total_checklists: int = 0) -> RiskAssessment:
    """
    Deterministically computes risk scores based on user profile and weather parameters.
    No LLM is used here. Rules are completely transparent and explainable.
    """
    risk_factors = []

    # 1. Weather Severity Calculation
    # WMO codes mapping to high risk:
    # 95, 96, 99: Thunderstorms
    # 82: Violent rain showers
    # 65: Heavy rain
    # 81: Moderate/Heavy rain showers
    rain_val = weather.rain + weather.showers
    wind = weather.wind_speed

    # Base weather severity points
    rain_points = min(rain_val * 4.0, 50.0) # Up to 50 pts for heavy rain
    wind_points = min(wind * 0.8, 30.0)      # Up to 30 pts for wind speed
    
    code_points = 0.0
    wmo = weather.weather_code
    if wmo in [82, 99]:
        code_points = 20.0
    elif wmo in [65, 81, 95, 96]:
        code_points = 15.0
    elif wmo in [51, 53, 55, 61, 63, 67, 80]:
        code_points = 10.0

    severity_score = min(rain_points + wind_points + code_points, 100.0)

    if severity_score >= 75.0 or wmo in [82, 99]:
        weather_level = RiskLevel.EXTREME
        weather_desc = f"Extreme weather event: Violent conditions with heavy rainfall ({rain_val:.1f} mm) and/or critical wind speeds ({wind:.1f} km/h). Immediate hazard warning."
        risk_factors.append("Extreme rainfall or high wind velocity")
    elif severity_score >= 55.0 or wmo in [65, 81, 95, 96]:
        weather_level = RiskLevel.HIGH
        weather_desc = f"High severity weather: Substantial rainfall ({rain_val:.1f} mm) and high winds ({wind:.1f} km/h) active. Severe disruptions expected."
        risk_factors.append("Heavy rainfall or strong winds")
    elif severity_score >= 25.0 or wmo in [51, 53, 55, 61, 63, 67, 80]:
        weather_level = RiskLevel.MODERATE
        weather_desc = f"Moderate severity weather: Light-to-moderate rain ({rain_val:.1f} mm) and breezy conditions ({wind:.1f} km/h). Standard safety precautions advised."
    else:
        weather_level = RiskLevel.LOW
        weather_desc = f"Low severity weather: Mild temperature ({weather.temperature:.1f}°C) and calm conditions. No immediate alerts."

    # 2. Flood Risk Calculation
    # Factors: rainfall, ground-floor dwelling, WMO weather codes.
    if weather_level == RiskLevel.EXTREME:
        if profile.lives_on_ground_floor:
            flood_level = RiskLevel.EXTREME
            flood_desc = f"Extreme Flood Risk. Living on the ground floor during severe weather ({rain_val:.1f} mm rain) presents high risk of water entering the home. Elevate belongings and secure utilities."
            risk_factors.append("Ground floor residence in extreme rainfall")
        else:
            flood_level = RiskLevel.HIGH
            flood_desc = f"High Flood Risk. Severe rain ({rain_val:.1f} mm) is highly likely to cause waterlogging and flooding of surrounding streets, blocking exits."
            risk_factors.append("Low-lying/Street waterlogging")
    elif weather_level == RiskLevel.HIGH:
        if profile.lives_on_ground_floor:
            flood_level = RiskLevel.HIGH
            flood_desc = f"High Flood Risk. Heavy rainfall ({rain_val:.1f} mm) creates risk for ground floor apartments. Monitor drainage channels closely."
            risk_factors.append("Ground floor residence in heavy rainfall")
        else:
            flood_level = RiskLevel.MODERATE
            flood_desc = f"Moderate Flood Risk. Heavy precipitation ({rain_val:.1f} mm) will cause water accumulation in street channels. Commuting is not recommended."
    elif weather_level == RiskLevel.MODERATE:
        if profile.lives_on_ground_floor:
            flood_level = RiskLevel.MODERATE
            flood_desc = f"Moderate Flood Risk. Wet weather active. Keep eye on local drains for blockage."
        else:
            flood_level = RiskLevel.LOW
            flood_desc = "Low Flood Risk. Minor water accumulation on roads, building structure remains secure."
    else:
        flood_level = RiskLevel.LOW
        flood_desc = "Low Flood Risk. Dry weather or light drizzle; no active flooding warnings in place."

    # 3. Travel Risk Calculation
    # Factors: travel_today, weather severity, vehicle_type, daily commute.
    if not profile.travel_today:
        travel_level = RiskLevel.LOW
        travel_desc = "Low Travel Risk. No travel planned for today, reducing overall transit exposure."
    else:
        if weather_level == RiskLevel.EXTREME:
            travel_level = RiskLevel.EXTREME
            travel_desc = f"Extreme Travel Risk. Winds of {wind:.1f} km/h and heavy rainfall ({rain_val:.1f} mm) make roads extremely hazardous. Postpone all non-emergency transit."
            risk_factors.append("Planned travel during extreme weather warnings")
        elif weather_level == RiskLevel.HIGH:
            if profile.vehicle_type == "2-Wheeler":
                travel_level = RiskLevel.HIGH
                travel_desc = "High Travel Risk. Heavy rain and winds are extremely hazardous for 2-wheelers due to low stability, slippery roads, and high skidding rates."
                risk_factors.append("2-wheeler transit in heavy rain")
            elif profile.vehicle_type == "4-Wheeler":
                travel_level = RiskLevel.MODERATE
                travel_desc = "Moderate Travel Risk. Heavy rain creates waterlogging and poor visibility. Safe in a 4-wheeler if speeds are reduced; watch for open manholes."
            else:
                travel_level = RiskLevel.HIGH
                travel_desc = "High Travel Risk. Public transportation systems and street walking are likely disrupted by severe waterlogging."
                risk_factors.append("Pedestrian/transit commuting in storm")
        elif weather_level == RiskLevel.MODERATE:
            if profile.vehicle_type == "2-Wheeler":
                travel_level = RiskLevel.MODERATE
                travel_desc = "Moderate Travel Risk. Roads are damp and braking times are extended. Commuters on two-wheelers must drive cautiously."
            else:
                travel_level = RiskLevel.LOW
                travel_desc = "Low Travel Risk. Wet conditions present, but transit remains safe under standard low-speed precautions."
        else:
            travel_level = RiskLevel.LOW
            travel_desc = "Low Travel Risk. Stable weather conditions. Safe to proceed with normal commutes."

    # 4. Health Risk Calculation
    # Factors: Age (children/seniors), medical conditions, temperature, humidity.
    is_vulnerable = profile.age >= 60 or profile.age < 5 or profile.has_seniors or profile.has_children or len(profile.medical_conditions) > 0
    has_respiratory = any(cond.lower() in ["asthma", "bronchitis", "copd", "respiratory"] for cond in profile.medical_conditions)
    has_joints = any(cond.lower() in ["arthritis", "gout", "joint pain", "joints"] for cond in profile.medical_conditions)

    if weather_level in [RiskLevel.EXTREME, RiskLevel.HIGH]:
        if is_vulnerable:
            health_level = RiskLevel.HIGH
            health_desc = "High Health Risk. High humidity, damp environment, and drafts can aggravate respiratory and joint symptoms. Exposure increases risk of infection for seniors/children."
            risk_factors.append("Vulnerable family profile in damp weather")
        else:
            health_level = RiskLevel.MODERATE
            health_desc = "Moderate Health Risk. Avoid exposure to stagnating water to prevent contact with vector-borne (dengue/malaria) and water-borne pathogens."
    else:
        if has_respiratory and weather.humidity > 80.0:
            health_level = RiskLevel.HIGH
            health_desc = f"High Health Risk. High relative humidity ({weather.humidity:.1f}%) triggers respiratory issues (such as asthma). Avoid outdoor drafts."
            risk_factors.append("Respiratory triggers due to high humidity")
        elif has_joints and weather.humidity > 80.0 and weather.temperature < 20.0:
            health_level = RiskLevel.MODERATE
            health_desc = f"Moderate Health Risk. Cold ({weather.temperature:.1f}°C) and damp conditions are likely to increase joint pain and muscle stiffness."
            risk_factors.append("Arthritis triggers due to cold and damp")
        elif weather_level == RiskLevel.MODERATE and is_vulnerable:
            health_level = RiskLevel.MODERATE
            health_desc = "Moderate Health Risk. Humidity and dampness can cause mild discomfort. Ensure children and seniors stay dry."
        else:
            health_level = RiskLevel.LOW
            health_desc = "Low Health Risk. Stable parameters. Standard wellness guidelines apply."

    # 5. Preparedness Score Calculation
    # Calculated out of 100 points
    # - Profile Completeness: 40 points (has name, age, city, and at least 1 emergency contact)
    # - Checklist completion: 60 points (prorated by checklist checked items)
    profile_score = 0
    if profile.name and profile.city and profile.state:
        profile_score += 20
    if len(profile.emergency_contacts) > 0:
        profile_score += 20
    
    checklist_score = 0
    if total_checklists > 0:
        checklist_score = int((completed_checklists / total_checklists) * 60)
    else:
        checklist_score = 60 # Default if checklist is empty / not initialized

    overall_score = profile_score + checklist_score

    return RiskAssessment(
        flood_risk_level=flood_level,
        flood_risk_desc=flood_desc,
        travel_risk_level=travel_level,
        travel_risk_desc=travel_desc,
        health_risk_level=health_level,
        health_risk_desc=health_desc,
        weather_severity_level=weather_level,
        weather_severity_desc=weather_desc,
        overall_preparedness_score=overall_score,
        risk_factors=risk_factors
    )

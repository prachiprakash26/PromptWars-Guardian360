from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    EXTREME = "Extreme"

class EmergencyContact(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    relation: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=7, max_length=15)

class UserProfile(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=0, le=120)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    lives_on_ground_floor: bool = False
    has_children: bool = False
    has_seniors: bool = False
    medical_conditions: List[str] = Field(default_factory=list)
    has_vehicle: bool = False
    vehicle_type: str = Field("None") # e.g. "None", "2-Wheeler", "4-Wheeler"
    daily_commute: bool = False
    commute_distance_km: float = Field(0.0, ge=0.0, le=500.0)
    preferred_language: str = Field("English", min_length=2, max_length=50)
    emergency_contacts: List[EmergencyContact] = Field(default_factory=list)
    travel_today: bool = False

class WeatherData(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    temperature: float
    humidity: float
    precipitation: float # in mm (sum of rain, showers)
    rain: float # in mm
    showers: float # in mm
    wind_speed: float # in km/h
    wind_gusts: float # in km/h
    weather_code: int # WMO code
    hourly_time: List[str] = Field(default_factory=list)
    hourly_precipitation: List[float] = Field(default_factory=list)
    hourly_temperature: List[float] = Field(default_factory=list)

class RiskAssessment(BaseModel):
    flood_risk_level: RiskLevel
    flood_risk_desc: str
    travel_risk_level: RiskLevel
    travel_risk_desc: str
    health_risk_level: RiskLevel
    health_risk_desc: str
    weather_severity_level: RiskLevel
    weather_severity_desc: str
    overall_preparedness_score: int # 0 to 100
    risk_factors: List[str] = Field(default_factory=list)

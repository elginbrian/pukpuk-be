from beanie import Document
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class ForecastData(Document):
    month: str
    actual: Optional[float]
    predicted: float
    crop_type: str
    region: str
    season: str

    class Settings:
        name = "forecast_data"

class Metrics(Document):
    mae: float
    rmse: float
    demand_trend: float
    volatility_score: float
    crop_type: str
    region: str
    season: str

    class Settings:
        name = "metrics"

class ChatSession(Document):
    session_id: str
    created_at: datetime
    last_activity: datetime
    crop_type: str = "rice"
    region: str = "jawa-barat"
    season: str = "wet-season"

    class Settings:
        name = "chat_sessions"

class ChatMessage(Document):
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    suggestions: Optional[List[str]] = None

    class Settings:
        name = "chat_messages"

class AIInsight(Document):
    user_query: str
    ai_response: str
    suggestions: List[str]
    crop_type: str
    region: str
    season: str
    created_at: datetime

    class Settings:
        name = "ai_insights"

class AIInsightRequest(BaseModel):
    query: str
    crop_type: str = "rice"
    region: str = "jawa-barat"
    season: str = "wet-season"

class AIInsightResponse(BaseModel):
    response: str
    suggestions: List[str]

# Route Optimization Entities
class RouteOption(BaseModel):
    id: str  # "fastest", "cheapest", "greenest"
    distance: float  # in km
    duration: str  # e.g., "3h 45min"
    fuel_cost: float  # in IDR
    toll_cost: float  # in IDR
    co2: float  # in kg
    path: str  # route description
    waypoints: List[List[float]]  # list of [lat, lng] coordinates

class RouteOptimizationRequest(BaseModel):
    origin: str
    destination: str
    vehicle_type: str
    load_capacity: float

class RouteOptimizationResponse(BaseModel):
    fastest: RouteOption
    cheapest: RouteOption
    greenest: RouteOption

# Route Data Entities for Database
class Location(Document):
    code: str  # e.g., "plant-a", "warehouse-b"
    name: str  # e.g., "Plant A - Karawang"
    coordinates: List[float]  # [latitude, longitude]
    type: str  # "plant", "warehouse", "kiosk"
    address: str
    icon_url: str  # URL to the marker icon

    class Settings:
        name = "locations"

class RouteConfiguration(Document):
    origin: str  # location code
    destination: str  # location code
    vehicle_type: str
    load_capacity: float
    fastest_distance: float
    cheapest_distance: float
    greenest_distance: float
    fastest_path: List[str]  # list of location codes
    cheapest_path: List[str]
    greenest_path: List[str]

    class Settings:
        name = "route_configurations"

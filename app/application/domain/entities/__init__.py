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

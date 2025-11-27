from beanie import Document
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

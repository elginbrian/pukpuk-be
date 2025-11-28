from beanie import Document
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ForecastData(Document):
    month: str
    actual: Optional[float]
    predicted: float
    upper_ci: Optional[float] = None
    lower_ci: Optional[float] = None
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
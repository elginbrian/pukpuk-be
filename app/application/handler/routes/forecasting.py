from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random 

router = APIRouter(prefix="/forecasting", tags=["forecasting"])

# Pydantic models
class ForecastData(BaseModel):
    month: str
    actual: Optional[float]
    predicted: float

class Metrics(BaseModel):
    mae: float
    rmse: float
    demand_trend: float
    volatility_score: float

class ForecastRequest(BaseModel):
    crop_type: str
    region: str
    season: str

class ScenarioRequest(BaseModel):
    rainfall_change: float

# Mock data generators
def generate_forecast_data(crop_type: str, region: str, season: str) -> List[ForecastData]:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    data = []
    base_demand = 4000 + random.randint(-500, 500)
    
    for i, month in enumerate(months):
        actual = base_demand + random.randint(-300, 300) if i < 6 else None
        predicted = base_demand + random.randint(-200, 400)
        data.append(ForecastData(month=month, actual=actual, predicted=predicted))
    
    return data

def generate_metrics() -> Metrics:
    return Metrics(
        mae=142 + random.uniform(-20, 20),
        rmse=218 + random.uniform(-30, 30),
        demand_trend=15.3 + random.uniform(-5, 5),
        volatility_score=0.68 + random.uniform(-0.1, 0.1)
    )

@router.get("/metrics", response_model=Metrics)
async def get_metrics():
    """Get current forecasting metrics"""
    return generate_metrics()

@router.post("/forecast", response_model=List[ForecastData])
async def run_forecast(request: ForecastRequest):
    """Run forecast with given parameters"""
    return generate_forecast_data(request.crop_type, request.region, request.season)

@router.post("/scenario", response_model=List[ForecastData])
async def simulate_scenario(request: ScenarioRequest):
    """Simulate scenario with rainfall change"""
    
    data = generate_forecast_data("rice", "jawa-barat", "wet-season")
    for item in data:
        if item.predicted:
            item.predicted *= (1 + request.rainfall_change / 100)
    return data
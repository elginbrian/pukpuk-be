from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.application.container import container
from app.application.use_cases import GetForecastUseCase, GetMetricsUseCase, SimulateScenarioUseCase

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

# Dependency injection
def get_forecast_use_case() -> GetForecastUseCase:
    return container.get_forecast_use_case()

def get_metrics_use_case() -> GetMetricsUseCase:
    return container.get_metrics_use_case()

def get_simulate_scenario_use_case() -> SimulateScenarioUseCase:
    return container.simulate_scenario_use_case()

@router.get("/metrics", response_model=Metrics)
async def get_metrics(
    crop_type: str = "rice",
    region: str = "jawa-barat",
    season: str = "wet-season",
    use_case: GetMetricsUseCase = Depends(get_metrics_use_case)
):
    """Get current forecasting metrics"""
    return await use_case.execute(crop_type, region, season)

@router.post("/forecast", response_model=List[ForecastData])
async def run_forecast(
    request: ForecastRequest,
    use_case: GetForecastUseCase = Depends(get_forecast_use_case)
):
    """Run forecast with given parameters"""
    data = await use_case.execute(request.crop_type, request.region, request.season)
    
    return [
        ForecastData(month=item.month, actual=item.actual, predicted=item.predicted)
        for item in data
    ]

@router.post("/scenario", response_model=List[ForecastData])
async def simulate_scenario(
    request: ScenarioRequest,
    use_case: SimulateScenarioUseCase = Depends(get_simulate_scenario_use_case)
):
    """Simulate scenario with rainfall change"""
    data = await use_case.execute(request.rainfall_change)
    # Convert to response model (exclude database fields)
    return [
        ForecastData(month=item.month, actual=item.actual, predicted=item.predicted)
        for item in data
    ]
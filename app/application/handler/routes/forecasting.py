from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
from app.application.container import container
from app.application.use_cases import GetForecastUseCase, GetMetricsUseCase, SimulateScenarioUseCase
from app.infrastructure.utils.export_service import ExportService

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

@router.get("/export")
async def export_forecast_results(
    crop_type: str = "rice",
    region: str = "jawa-barat", 
    season: str = "wet-season",
    format: str = "csv",
    forecast_use_case: GetForecastUseCase = Depends(get_forecast_use_case),
    metrics_use_case: GetMetricsUseCase = Depends(get_metrics_use_case)
):
    """Export forecast results to CSV or JSON format"""
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    # Get forecast data and metrics
    forecast_data = await forecast_use_case.execute(crop_type, region, season)
    metrics = await metrics_use_case.execute(crop_type, region, season)
    
    if format == "csv":
        csv_content = ExportService.export_forecast_to_csv(forecast_data, metrics)
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=forecast_{crop_type}_{region}_{season}.csv"}
        )
    else:  # json
        json_data = ExportService.export_forecast_to_json(forecast_data, metrics)
        return json_data
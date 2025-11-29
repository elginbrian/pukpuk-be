from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List
from app.application.use_cases.demand_heatmap import GetDemandHeatmapDataUseCase
from app.application.use_cases.maps import MapsUseCase
from app.infrastructure.repositories.maps import MapsRepository
from app.infrastructure.database.database import get_database
import os

router = APIRouter()

# Pydantic models for demand heatmap data
class MapAnalyticsData(BaseModel):
    status: str  # "critical" | "warning" | "safe" | "overstock" | "unknown"
    value: float
    label: str

class RegionalInsight(BaseModel):
    name: str
    code: str
    demand: str
    confidence: int
    trend: str  # "up" | "down" | "stable"
    risk: str   # "low" | "medium" | "high"

class DemandHeatmapResponse(BaseModel):
    mapAnalytics: Dict[str, MapAnalyticsData]
    regionalInsights: List[RegionalInsight]

# Dependency injection functions
def get_maps_use_case() -> MapsUseCase:
    return MapsUseCase(MapsRepository(get_database()))

def get_demand_heatmap_use_case() -> GetDemandHeatmapDataUseCase:
    from app.application.container import container
    return container.get_demand_heatmap_data_use_case()

@router.get("/maps/{filename}")
async def get_geojson(filename: str):
    if not filename.endswith('.geojson'):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = os.path.join("data", "maps", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type='application/json')

@router.get("/region-mappings")
async def get_region_mappings(
    maps_use_case: MapsUseCase = Depends(get_maps_use_case)
):
    """Get region to geojson filename mappings."""
    return await maps_use_case.get_region_mappings()

@router.get("/demand-data", response_model=DemandHeatmapResponse)
async def get_demand_heatmap_data(
    level: str = Query(..., description="Region level (pulau, province code, etc.)"),
    mode: str = Query(..., description="Data mode (live or forecast)"),
    layer: str = Query(..., description="Data layer (demand, stock, etc.)"),
    use_case: GetDemandHeatmapDataUseCase = Depends(get_demand_heatmap_use_case)
):
    """Get demand heatmap data including map analytics and regional insights."""
    result = await use_case.execute(level, mode, layer)
    return result
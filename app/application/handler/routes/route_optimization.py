from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.application.container import container
from app.application.use_cases import OptimizeRouteUseCase, GetLocationsUseCase
from app.application.domain.entities import RouteOptimizationRequest, RouteOptimizationResponse, Location

router = APIRouter(prefix="/route-optimization", tags=["route-optimization"])

# Dependency injection
def get_optimize_route_use_case() -> OptimizeRouteUseCase:
    return container.optimize_route_use_case()

def get_locations_use_case() -> GetLocationsUseCase:
    return container.get_locations_use_case()

@router.post("/optimize", response_model=RouteOptimizationResponse)
async def optimize_route(
    request: RouteOptimizationRequest,
    use_case: OptimizeRouteUseCase = Depends(get_optimize_route_use_case)
):
    """
    Optimize routes based on origin, destination, vehicle type, and load capacity.
    Returns three route options: fastest, cheapest, and greenest.
    """
    try:
        return await use_case.execute(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@router.get("/locations", response_model=List[Location])
async def get_locations(
    use_case: GetLocationsUseCase = Depends(get_locations_use_case)
):
    """
    Get all available locations for route optimization.
    Returns a list of locations with their coordinates, types, and addresses.
    """
    try:
        return await use_case.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get locations: {str(e)}")
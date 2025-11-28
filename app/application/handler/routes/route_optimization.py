from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.application.container import container
from app.application.use_cases import OptimizeRouteUseCase, GetLocationsUseCase, GetVehiclesUseCase, GetRouteConfigurationsUseCase
from app.application.domain.entities import RouteOptimizationRequest, RouteOptimizationResponse, Location, Vehicle, RouteConfiguration

router = APIRouter(prefix="/route-optimization", tags=["route-optimization"])

# Dependency injection
def get_optimize_route_use_case() -> OptimizeRouteUseCase:
    return container.optimize_route_use_case()

def get_locations_use_case() -> GetLocationsUseCase:
    return container.get_locations_use_case()

def get_vehicles_use_case() -> GetVehiclesUseCase:
    return container.get_vehicles_use_case()

def get_route_configurations_use_case() -> GetRouteConfigurationsUseCase:
    return container.get_route_configurations_use_case()

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

@router.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(
    use_case: GetVehiclesUseCase = Depends(get_vehicles_use_case)
):
    """
    Get all available vehicles for route optimization.
    Returns a list of vehicles with their specifications.
    """
    try:
        return await use_case.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vehicles: {str(e)}")

@router.get("/configurations", response_model=List[RouteConfiguration])
async def get_route_configurations(
    use_case: GetRouteConfigurationsUseCase = Depends(get_route_configurations_use_case)
):
    """
    Get all route configurations.
    Returns a list of predefined route configurations.
    """
    try:
        return await use_case.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get route configurations: {str(e)}")
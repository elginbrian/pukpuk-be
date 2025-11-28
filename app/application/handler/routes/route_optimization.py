from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import httpx
from app.application.container import container
from app.application.use_cases import OptimizeRouteUseCase, GetLocationsUseCase, GetVehiclesUseCase, GetRouteConfigurationsUseCase
from app.application.domain.entities import RouteOptimizationRequest, RouteOptimizationResponse, Location, Vehicle, RouteConfiguration

router = APIRouter(prefix="/route-optimization", tags=["route-optimization"])

# Pydantic models for routing
class RouteDirectionsRequest(BaseModel):
    origin_coords: List[float]  # [lat, lng]
    dest_coords: List[float]   # [lat, lng]

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

@router.post("/directions")
async def get_route_directions(request: RouteDirectionsRequest):
    """
    Get actual road route directions between two coordinates using OpenRouteService.
    Returns GeoJSON with route geometry.
    """
    try:
       
        ORS_API_KEY = "5b3ce3597851110001cf6248d5c6e4c6b4c40b8b9b8c4f4b8c4f4b8c4f4b8c4f4b"  # Public demo key
        url = f"https://api.openrouteservice.org/v2/directions/driving-car?api_key={ORS_API_KEY}&start={request.origin_coords[1]},{request.origin_coords[0]}&end={request.dest_coords[1]},{request.dest_coords[0]}&format=geojson"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [request.origin_coords[1], request.origin_coords[0]],
                    [request.dest_coords[1], request.dest_coords[0]]
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get route directions: {str(e)}")
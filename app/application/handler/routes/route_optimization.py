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
    Get actual road route directions between two coordinates using OSRM.
    Returns GeoJSON with route geometry.
    """
    try:
    
        start_lng, start_lat = request.origin_coords[1], request.origin_coords[0]
        end_lng, end_lat = request.dest_coords[1], request.dest_coords[0]

        url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"

        print(f"Calling OSRM: {url}")  # Debug logging

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            print(f"OSRM response status: {response.status_code}")  # Debug logging

            if response.status_code == 200:
                data = response.json()
                print(f"OSRM response: {data}")  # Debug logging

                if data.get('routes') and len(data['routes']) > 0:
                    route = data['routes'][0]
                    return {
                        "type": "Feature",
                        "geometry": route['geometry'],
                        "properties": {
                            "distance": route.get('distance'),
                            "duration": route.get('duration')
                        }
                    }
                else:
                    raise Exception("No routes found in OSRM response")
            else:
                print(f"OSRM error: {response.status_code} - {response.text}")
                raise httpx.HTTPStatusError("API call failed", request=None, response=response)

    except Exception as e:
        print(f"OSRM failed: {str(e)}") 
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [request.origin_coords[1], request.origin_coords[0]],
                    [request.dest_coords[1], request.dest_coords[0]]
                ]
            },
            "properties": {
                "fallback": True
            }
        }
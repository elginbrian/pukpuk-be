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
    route_type: str = "fastest"  # fastest, cheapest, greenest

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
    Route geometry varies based on route_type: fastest, cheapest, greenest.
    Returns GeoJSON with route geometry.
    """
    try:
        start_lng, start_lat = request.origin_coords[1], request.origin_coords[0]
        end_lng, end_lat = request.dest_coords[1], request.dest_coords[0]

        route_config = None
        try:
            from app.infrastructure.database.database import get_database_sync
            db = get_database_sync()
            if db:
                from app.application.domain.entities.route_optimization import RouteConfiguration

                locations = await get_locations_use_case()().execute()

                def find_closest_location(target_coords: List[float]) -> str:
                    """Find the location code closest to target coordinates."""
                    closest_loc = None
                    min_distance = float('inf')

                    for loc in locations:
                        # Calculate simple distance (could be improved with haversine)
                        distance = ((loc.coordinates[0] - target_coords[0]) ** 2 +
                                  (loc.coordinates[1] - target_coords[1]) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            closest_loc = loc.code

                    return closest_loc or "plant-surabaya"  # fallback

                origin_code = find_closest_location(request.origin_coords)
                dest_code = find_closest_location(request.dest_coords)

                print(f"Looking for route config: {origin_code} -> {dest_code}")

                route_config = await RouteConfiguration.find(
                    RouteConfiguration.origin == origin_code,
                    RouteConfiguration.destination == dest_code,
                    RouteConfiguration.vehicle_type == "truck-medium",  # Default vehicle type
                    RouteConfiguration.load_capacity == 8.0  # Default load capacity
                ).first_or_none()

                if route_config:
                    print(f"Found route config: {route_config.origin} -> {route_config.destination}")
                else:
                    print(f"No route config found for {origin_code} -> {dest_code}")

        except Exception as e:
            print(f"Database lookup failed: {e}")

        # Build waypoints based on route type
        waypoints = []

        if route_config and request.route_type in ["fastest", "cheapest", "greenest"]:
            # Use database waypoints
            path_codes = getattr(route_config, f"{request.route_type}_path", [])
            locations_use_case = get_locations_use_case()
            locations = await locations_use_case.execute()

            for code in path_codes:
                loc = next((l for l in locations if l.code == code), None)
                if loc:
                    waypoints.append(f"{loc.coordinates[1]},{loc.coordinates[0]}")  # lng,lat
        else:
            # Fallback to direct route
            waypoints = [f"{start_lng},{start_lat}", f"{end_lng},{end_lat}"]

        # Ensure we have at least start and end
        if len(waypoints) < 2:
            waypoints = [f"{start_lng},{start_lat}", f"{end_lng},{end_lat}"]

        waypoints_str = ";".join(waypoints)
        url = f"https://router.project-osrm.org/route/v1/driving/{waypoints_str}?overview=full&geometries=geojson&alternatives=false"

        print(f"Calling OSRM for {request.route_type} with waypoints: {url}")  # Debug logging

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
                            "duration": route.get('duration'),
                            "route_type": request.route_type
                        }
                    }
                else:
                    raise Exception("No routes found in OSRM response")
            else:
                print(f"OSRM error: {response.status_code} - {response.text}")
                raise httpx.HTTPStatusError("API call failed", request=None, response=response)

    except Exception as e:
        print(f"OSRM failed for {request.route_type}: {str(e)}")
       
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
                "fallback": True,
                "route_type": request.route_type
            }
        }
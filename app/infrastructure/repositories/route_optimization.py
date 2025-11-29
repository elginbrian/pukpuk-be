from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities.route_optimization import RouteOptimizationRequest, RouteOptimizationResponse, RouteOption, Location, RouteConfiguration, Vehicle
from ...application.domain.interfaces.route_optimization import IRouteOptimizationRepository
from ..database.database import is_database_available
import math
from collections import defaultdict
import heapq

class RouteOptimizationRepository(IRouteOptimizationRepository):
    def __init__(self, database: Optional[AsyncIOMotorDatabase]):
        self.database = database

    def _haversine_distance(self, coord1: List[float], coord2: List[float]) -> float:
        """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
        # Convert decimal degrees to radians
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    def _dijkstra(self, graph: dict, start: str, end: str, weight_func) -> tuple:
        """Dijkstra's algorithm to find shortest path"""
        queue = []  # (cost, node, path, distance)
        heapq.heappush(queue, (0, start, [], 0))
        visited = set()
        min_cost = {start: 0}

        while queue:
            cost, node, path, dist = heapq.heappop(queue)
            if node in visited:
                continue
            visited.add(node)
            path = path + [node]

            if node == end:
                return cost, path, dist

            for neighbor, edge_data in graph.get(node, {}).items():
                if neighbor in visited:
                    continue
                new_cost = cost + weight_func(edge_data)
                new_dist = dist + edge_data['distance']
                if new_cost < min_cost.get(neighbor, float('inf')):
                    min_cost[neighbor] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor, path, new_dist))

        return float('inf'), [], 0  # No path found

    def _build_graph(self, locations: List[Location]) -> dict:
        """Build a graph where nodes are location codes and edges have distance"""
        graph = defaultdict(dict)
        loc_dict = {loc.code: loc for loc in locations}

        for loc1 in locations:
            for loc2 in locations:
                if loc1.code != loc2.code:
                    dist = self._haversine_distance(loc1.coordinates, loc2.coordinates)
                    graph[loc1.code][loc2.code] = {
                        'distance': dist,
                        'coord1': loc1.coordinates,
                        'coord2': loc2.coordinates
                    }
        return graph

    async def _get_locations(self) -> List[Location]:
        """Get locations from database or mock"""
        if self.database is not None and is_database_available():
            try:
                return await Location.find().to_list()
            except:
                pass
        # Mock locations
        return [
            Location(code="plant-a", name="Plant A - Karawang", coordinates=[-6.3074, 107.3103], type="plant", address="Karawang", icon_url="https://example.com/plant.png"),
            Location(code="plant-b", name="Plant B - Surabaya", coordinates=[-7.1612, 112.6535], type="plant", address="Surabaya", icon_url="https://example.com/plant.png"),
            Location(code="warehouse-a", name="Warehouse A - Jakarta", coordinates=[-6.2088, 106.8166], type="warehouse", address="Jakarta", icon_url="https://example.com/warehouse.png"),
            Location(code="warehouse-b", name="Warehouse B - Bandung", coordinates=[-6.595, 106.8166], type="warehouse", address="Bandung", icon_url="https://example.com/warehouse.png"),
            Location(code="kios-bandung", name="Kios Bandung", coordinates=[-6.9175, 107.6191], type="kiosk", address="Bandung", icon_url="https://example.com/kiosk.png"),
            Location(code="kios-tasikmalaya", name="Kios Tasikmalaya", coordinates=[-7.3156, 108.2048], type="kiosk", address="Tasikmalaya", icon_url="https://example.com/kiosk.png"),
            Location(code="kios-sumedang", name="Kios Sumedang", coordinates=[-6.9858, 107.8148], type="kiosk", address="Sumedang", icon_url="https://example.com/kiosk.png"),
            Location(code="kios-garut", name="Kios Garut", coordinates=[-7.207, 107.9177], type="kiosk", address="Garut", icon_url="https://example.com/kiosk.png"),
        ]

    async def _get_vehicles(self) -> List[Vehicle]:
        """Get vehicles from database or mock"""
        if self.database is not None and is_database_available():
            try:
                return await Vehicle.find().to_list()
            except:
                pass
        # Mock vehicles
        return [
            Vehicle(code="truck-small", name="Small Truck (3-5 tons)", min_capacity=3, max_capacity=5, fuel_consumption=8, average_speed=60, co2_factor=0.35, type="truck"),
            Vehicle(code="truck-medium", name="Medium Truck (5-8 tons)", min_capacity=5, max_capacity=8, fuel_consumption=6, average_speed=55, co2_factor=0.4, type="truck"),
            Vehicle(code="truck-large", name="Large Truck (8-12 tons)", min_capacity=8, max_capacity=12, fuel_consumption=5, average_speed=50, co2_factor=0.45, type="truck"),
        ]

    async def _compute_optimized_routes(self, request: RouteOptimizationRequest, locations: List[Location], location_dict: dict, vehicle: Vehicle) -> RouteOptimizationResponse:
        """Compute optimized routes directly from origin to destination"""
        origin_loc = location_dict[request.origin]
        dest_loc = location_dict[request.destination]

        direct_distance = self._haversine_distance(origin_loc.coordinates, dest_loc.coordinates)

        # Adjust for load capacity (higher load = slower speed, higher fuel consumption)
        load_factor = min(1.0 + (request.load_capacity - vehicle.min_capacity) / (vehicle.max_capacity - vehicle.min_capacity), 1.5)
        adjusted_speed = vehicle.average_speed / load_factor
        adjusted_fuel_consumption = vehicle.fuel_consumption * load_factor

        # Fuel price per liter (IDR)
        fuel_price = 15000

        # Toll cost per km (approximate) - varies by route type
        base_toll_cost_per_km = 500

        # For different route optimizations:
        # Fastest: direct route, highest speed, higher tolls (expressways), normal fuel efficiency
        # Cheapest: longer route but uses cheaper roads with lower tolls, optimized fuel efficiency
        # Greenest: moderate distance, lower speed for better fuel efficiency, balanced tolls

        fastest_dist = direct_distance
        cheapest_dist = direct_distance * 1.1  # 10% longer
        greenest_dist = direct_distance * 1.05  # 5% longer

        # Create route options with different cost factors
        fastest = self._create_route_option(
            "fastest", fastest_dist, [request.origin, request.destination], location_dict,
            adjusted_speed, adjusted_fuel_consumption, fuel_price, base_toll_cost_per_km * 1.2,  # Higher tolls for expressways
            vehicle.co2_factor, load_factor
        )
        cheapest = self._create_route_option(
            "cheapest", cheapest_dist, [request.origin, request.destination], location_dict,
            adjusted_speed * 0.9, adjusted_fuel_consumption * 0.95, fuel_price, base_toll_cost_per_km * 0.7,  # Lower tolls for regular roads, better fuel efficiency
            vehicle.co2_factor, load_factor
        )
        greenest = self._create_route_option(
            "greenest", greenest_dist, [request.origin, request.destination], location_dict,
            adjusted_speed * 0.8, adjusted_fuel_consumption * 0.9, fuel_price, base_toll_cost_per_km * 0.9,  # Moderate tolls, best fuel efficiency
            vehicle.co2_factor * 0.9, load_factor  # Lower CO2 factor for greenest
        )

        return RouteOptimizationResponse(fastest=fastest, cheapest=cheapest, greenest=greenest)

    def _create_route_option(self, option_type: str, distance: float, path: List[str], location_dict: dict, speed: float, fuel_consumption: float, fuel_price: float, toll_cost_per_km: float, co2_factor: float, load_factor: float) -> RouteOption:
        """Create a RouteOption from computed data"""
        duration_hours = distance / speed
        hours = int(duration_hours)
        minutes = int((duration_hours - hours) * 60)
        duration = f"{hours}h {minutes}min"

        fuel_cost = distance * fuel_price * fuel_consumption
        toll_cost = distance * toll_cost_per_km
        co2 = distance * co2_factor / load_factor

        # Create simple path description from origin to destination
        if len(path) >= 2:
            origin_name = location_dict.get(path[0], {}).name if path[0] in location_dict else path[0]
            dest_name = location_dict.get(path[-1], {}).name if path[-1] in location_dict else path[-1]
            path_str = f"{origin_name} → {dest_name}"
        else:
            path_str = "Invalid path"

        return RouteOption(
            id=option_type,
            distance=round(distance, 1),
            duration=duration,
            fuel_cost=round(fuel_cost),
            toll_cost=round(toll_cost),
            co2=round(co2, 1),
            path=path_str
        )

    async def optimize_route(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        # Get locations and vehicles
        locations = await self._get_locations()
        location_dict = {loc.code: loc for loc in locations}

        # Validate origin and destination
        if request.origin not in location_dict or request.destination not in location_dict:
            raise ValueError(f"Invalid origin or destination: {request.origin} or {request.destination}")

        # Get vehicle data
        vehicles = await self._get_vehicles()
        vehicle_dict = {v.code: v for v in vehicles}
        if request.vehicle_type not in vehicle_dict:
            raise ValueError(f"Invalid vehicle type: {request.vehicle_type}")
        vehicle = vehicle_dict[request.vehicle_type]

        # Try to get data from database first
        if self.database is not None and is_database_available():
            try:
                route_config = await RouteConfiguration.find(
                    RouteConfiguration.origin == request.origin,
                    RouteConfiguration.destination == request.destination,
                    RouteConfiguration.vehicle_type == request.vehicle_type,
                    RouteConfiguration.load_capacity == request.load_capacity
                ).first_or_none()

                if route_config:
                    # Use database data
                    return await self._generate_from_database(request, route_config, location_dict, vehicle)
            except Exception as e:
                print(f"Database error in route optimization: {e}")

        # Compute optimized routes using algorithm
        return await self._compute_optimized_routes(request, locations, location_dict, vehicle)

    async def _generate_from_database(self, request: RouteOptimizationRequest, route_config: RouteConfiguration, location_dict: dict, vehicle: Vehicle) -> RouteOptimizationResponse:
        # Adjust based on load capacity
        load_factor = min(1.0 + (request.load_capacity - vehicle.min_capacity) / (vehicle.max_capacity - vehicle.min_capacity), 1.5)
        adjusted_speed = vehicle.average_speed / load_factor
        adjusted_fuel_consumption = vehicle.fuel_consumption * load_factor

        fuel_price = 15000
        toll_cost_per_km = 500

        # Generate route options using database data
        fastest = self._create_route_option_from_db(
            "fastest", route_config.fastest_distance, route_config.fastest_path, location_dict, adjusted_speed, adjusted_fuel_consumption, fuel_price, toll_cost_per_km, vehicle.co2_factor, load_factor
        )
        cheapest = self._create_route_option_from_db(
            "cheapest", route_config.cheapest_distance, route_config.cheapest_path, location_dict, adjusted_speed, adjusted_fuel_consumption, fuel_price, toll_cost_per_km, vehicle.co2_factor, load_factor
        )
        greenest = self._create_route_option_from_db(
            "greenest", route_config.greenest_distance, route_config.greenest_path, location_dict, adjusted_speed, adjusted_fuel_consumption, fuel_price, toll_cost_per_km, vehicle.co2_factor, load_factor
        )

        return RouteOptimizationResponse(
            fastest=fastest,
            cheapest=cheapest,
            greenest=greenest
        )

    def _create_route_option_from_db(self, option_type: str, distance: float, path_codes: List[str], location_dict: dict, speed: float, fuel_consumption: float, fuel_price: float, toll_cost_per_km: float, co2_factor: float, load_factor: float) -> RouteOption:
        # Generate waypoints from path codes
        waypoints = []
        for code in path_codes:
            if code in location_dict:
                waypoints.append(location_dict[code].coordinates)

        # Calculate based on option type (but use vehicle data)
        if option_type == "fastest":
            duration_hours = distance / speed
        elif option_type == "cheapest":
            duration_hours = distance / (speed * 0.8)  # Slightly slower for cheapest
        else:  # greenest
            duration_hours = distance / (speed * 0.9)  # Moderate speed for greenest

        fuel_cost = distance * fuel_price * fuel_consumption
        toll_cost = distance * toll_cost_per_km
        co2 = distance * co2_factor / load_factor

        hours = int(duration_hours)
        minutes = int((duration_hours - hours) * 60)
        duration = f"{hours}h {minutes}min"

        # Generate path description
        path_names = []
        for code in path_codes:
            if code in location_dict:
                path_names.append(location_dict[code].name)
        path = " → ".join(path_names)

        return RouteOption(
            id=option_type,
            distance=round(distance, 1),
            duration=duration,
            fuel_cost=int(fuel_cost),
            toll_cost=int(toll_cost),
            co2=round(co2, 1),
            path=path,
            waypoints=waypoints
        )

    async def get_locations(self) -> List[Location]:
        """Get all locations from database, fallback to mock data if database unavailable."""
        if self.database is not None and is_database_available():
            try:
                locations = await Location.find().to_list()
                return locations
            except Exception as e:
                print(f"Database error getting locations: {e}")
        return await self._get_locations()

    async def get_vehicles(self) -> List[Vehicle]:
        """Get all vehicles from database, fallback to mock data if database unavailable."""
        if self.database is not None and is_database_available():
            try:
                vehicles = await Vehicle.find().to_list()
                return vehicles
            except Exception as e:
                print(f"Database error getting vehicles: {e}")
        return await self._get_vehicles()

    async def get_route_configurations(self) -> List[RouteConfiguration]:
        """Get all route configurations from database, fallback to empty list if database unavailable."""
        if self.database is not None and is_database_available():
            try:
                configs = await RouteConfiguration.find().to_list()
                return configs
            except Exception as e:
                print(f"Database error getting route configurations: {e}")
                return []
        return []
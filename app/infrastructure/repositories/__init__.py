from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities import ForecastData, Metrics, AIInsight, ChatSession, ChatMessage, RouteOptimizationRequest, RouteOptimizationResponse, RouteOption, Location, RouteConfiguration, Vehicle
from ...application.domain.interfaces import IForecastRepository, IMetricsRepository, IAIInsightsRepository, IChatSessionRepository, IRouteOptimizationRepository
from ..database.database import is_database_available
import uuid
from datetime import datetime
import random

class ForecastRepository(IForecastRepository):
    def __init__(self, database: Optional[AsyncIOMotorDatabase]):
        self.database = database

    async def get_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        if self.database is None or not is_database_available():
            return []  
        
        data = await ForecastData.find(
            ForecastData.crop_type == crop_type,
            ForecastData.region == region,
            ForecastData.season == season
        ).to_list()
        
        return data

    async def save_forecast_data(self, data: List[ForecastData]) -> None:
        if self.database is not None and is_database_available() and data:
            await ForecastData.insert_many(data)

class MetricsRepository(IMetricsRepository):
    def __init__(self, database: Optional[AsyncIOMotorDatabase]):
        self.database = database

    async def get_latest_metrics(self, crop_type: str, region: str, season: str) -> Metrics:
        if self.database is None or not is_database_available():
            return Metrics(
                mae=0.0,
                rmse=0.0,
                demand_trend=0.0,
                volatility_score=0.0,
                crop_type=crop_type,
                region=region,
                season=season
            )  # Return zero values when database not available
        
        metrics = await Metrics.find(
            Metrics.crop_type == crop_type,
            Metrics.region == region,
            Metrics.season == season
        ).first_or_none()
        
        if metrics is None:
            return Metrics(
                mae=0.0,
                rmse=0.0,
                demand_trend=0.0,
                volatility_score=0.0,
                crop_type=crop_type,
                region=region,
                season=season
            )
        
        return metrics

    async def save_metrics(self, metrics: Metrics) -> None:
        if self.database is not None and is_database_available():
            await metrics.insert()

class AIInsightsRepository(IAIInsightsRepository):
    def __init__(self, database: Optional[AsyncIOMotorDatabase]):
        self.database = database

    async def save_insight(self, insight: AIInsight) -> None:
        if self.database is not None and is_database_available():
            await insight.insert()

    async def get_recent_insights(self, crop_type: str, region: str, season: str, limit: int = 10) -> List[AIInsight]:
        if self.database is None or not is_database_available():
            return []

        insights = await AIInsight.find(
            AIInsight.crop_type == crop_type,
            AIInsight.region == region,
            AIInsight.season == season
        ).sort(-AIInsight.created_at).limit(limit).to_list()

        return insights

class ChatSessionRepository(IChatSessionRepository):
    def __init__(self, database: Optional[AsyncIOMotorDatabase]):
        self.database = database

    async def create_session(self, crop_type: str, region: str, season: str) -> ChatSession:
        from datetime import datetime
        
        if self.database is None or not is_database_available():
           
            # Create a mock object with the same interface
            class MockChatSession:
                def __init__(self, session_id, created_at, last_activity, crop_type, region, season):
                    self.session_id = session_id
                    self.created_at = created_at
                    self.last_activity = last_activity
                    self.crop_type = crop_type
                    self.region = region
                    self.season = season
            
            return MockChatSession(
                session_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                crop_type=crop_type,
                region=region,
                season=season
            )
        
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            crop_type=crop_type,
            region=region,
            season=season
        )
        
        await session.insert()
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        if self.database is None or not is_database_available():
            return None
        
        return await ChatSession.find(ChatSession.session_id == session_id).first_or_none()

    async def update_session_activity(self, session_id: str) -> None:
        if self.database is None or not is_database_available():
            return
        
        await ChatSession.find(ChatSession.session_id == session_id).update(
            {"$set": {"last_activity": datetime.utcnow()}}
        )

    async def save_message(self, message: ChatMessage) -> None:
        if self.database is not None and is_database_available():
            await message.insert()

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        if self.database is None or not is_database_available():
            return []
        
        messages = await ChatMessage.find(
            ChatMessage.session_id == session_id
        ).sort(ChatMessage.timestamp).limit(limit).to_list()
        
        return messages


class RouteOptimizationRepository(IRouteOptimizationRepository):
    def __init__(self, database: Optional[AsyncIOMotorDatabase]):
        self.database = database

    async def optimize_route(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        # Try to get data from database first
        if self.database is not None and is_database_available():
            try:
                # Get locations from database
                locations = await Location.find().to_list()
                location_dict = {loc.code: loc for loc in locations}

                # Get route configuration from database
                route_config = await RouteConfiguration.find(
                    RouteConfiguration.origin == request.origin,
                    RouteConfiguration.destination == request.destination,
                    RouteConfiguration.vehicle_type == request.vehicle_type,
                    RouteConfiguration.load_capacity == request.load_capacity
                ).first_or_none()

                if route_config and request.origin in location_dict and request.destination in location_dict:
                    # Use database data
                    return await self._generate_from_database(request, route_config, location_dict)
            except Exception as e:
                # Log error and fall back to mock data
                print(f"Database error in route optimization: {e}")

        # Fall back to mock data
        return await self._generate_mock_response(request)

    async def _generate_from_database(self, request: RouteOptimizationRequest, route_config: RouteConfiguration, location_dict: dict) -> RouteOptimizationResponse:
        # Adjust distances based on vehicle type and load capacity
        vehicle_multiplier = {
            "truck-small": 1.0,
            "truck-medium": 1.1,
            "truck-large": 1.2,
        }.get(request.vehicle_type, 1.0)

        load_factor = min(1.0 + (request.load_capacity - 5) * 0.05, 1.3)  # Max 30% increase

        # Generate route options using database data
        fastest = await self._generate_route_option_from_db(
            "fastest", route_config.fastest_distance * vehicle_multiplier * load_factor,
            route_config.fastest_path, location_dict, request.origin, request.destination
        )
        cheapest = await self._generate_route_option_from_db(
            "cheapest", route_config.cheapest_distance * vehicle_multiplier * load_factor,
            route_config.cheapest_path, location_dict, request.origin, request.destination
        )
        greenest = await self._generate_route_option_from_db(
            "greenest", route_config.greenest_distance * vehicle_multiplier * load_factor,
            route_config.greenest_path, location_dict, request.origin, request.destination
        )

        return RouteOptimizationResponse(
            fastest=fastest,
            cheapest=cheapest,
            greenest=greenest
        )

    async def _generate_route_option_from_db(self, option_type: str, distance: float, path_codes: List[str], location_dict: dict, origin: str, destination: str) -> RouteOption:
        # Generate waypoints from path codes
        waypoints = []
        for code in path_codes:
            if code in location_dict:
                waypoints.append(location_dict[code].coordinates)

        # Calculate costs and emissions based on option type
        if option_type == "fastest":
            duration_hours = distance / 60  # 60 km/h average speed
            fuel_cost = distance * 12000  # IDR per km
            toll_cost = 45000
            co2 = distance * 0.35  # kg CO2 per km
        elif option_type == "cheapest":
            duration_hours = distance / 45  # 45 km/h average speed
            fuel_cost = distance * 10000  # IDR per km
            toll_cost = 25000
            co2 = distance * 0.4  # kg CO2 per km
        else:  # greenest
            duration_hours = distance / 50  # 50 km/h average speed
            fuel_cost = distance * 11000  # IDR per km
            toll_cost = 35000
            co2 = distance * 0.3  # kg CO2 per km

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

    async def _generate_mock_response(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        # Mock route optimization logic (fallback)
        # Base distances and times (mock data)
        base_distances = {
            ("plant-a", "kios-garut"): {"fastest": 245, "cheapest": 280, "greenest": 260},
            ("plant-a", "kios-bandung"): {"fastest": 180, "cheapest": 220, "greenest": 200},
            ("plant-a", "kios-tasikmalaya"): {"fastest": 150, "cheapest": 190, "greenest": 170},
            ("plant-a", "kios-sumedang"): {"fastest": 120, "cheapest": 160, "greenest": 140},
        }

        origin_dest = (request.origin, request.destination)
        distances = base_distances.get(origin_dest, {"fastest": 200, "cheapest": 250, "greenest": 230})

        # Adjust based on vehicle type and load capacity
        vehicle_multiplier = {
            "truck-small": 1.0,
            "truck-medium": 1.1,
            "truck-large": 1.2,
        }.get(request.vehicle_type, 1.0)

        load_factor = min(1.0 + (request.load_capacity - 5) * 0.05, 1.3)  # Max 30% increase

        # Generate route options
        fastest = self._generate_route_option("fastest", distances["fastest"] * vehicle_multiplier * load_factor, request.origin, request.destination)
        cheapest = self._generate_route_option("cheapest", distances["cheapest"] * vehicle_multiplier * load_factor, request.origin, request.destination)
        greenest = self._generate_route_option("greenest", distances["greenest"] * vehicle_multiplier * load_factor, request.origin, request.destination)

        return RouteOptimizationResponse(
            fastest=fastest,
            cheapest=cheapest,
            greenest=greenest
        )

    def _generate_route_option(self, option_type: str, distance: float, origin: str, destination: str) -> RouteOption:
        # Mock route generation logic with waypoints
        locations = {
            "plant-a": [-6.3074, 107.3103],
            "plant-b": [-7.1612, 112.6535],
            "warehouse-a": [-6.2088, 106.8166],
            "warehouse-b": [-6.595, 106.8166],
            "kios-bandung": [-6.9175, 107.6191],
            "kios-tasikmalaya": [-7.3156, 108.2048],
            "kios-sumedang": [-6.9858, 107.8148],
            "kios-garut": [-7.207, 107.9177],
        }

        if option_type == "fastest":
            duration_hours = distance / 60  # 60 km/h average speed
            fuel_cost = distance * 12000  # IDR per km
            toll_cost = 45000
            co2 = distance * 0.35  # kg CO2 per km
            waypoints = [
                locations.get(origin, locations["plant-a"]),
                locations.get("warehouse-b", locations["warehouse-b"]),
                locations.get("kios-bandung", locations["kios-bandung"]),
                locations.get(destination, locations["kios-garut"])
            ]
            path = f"{origin.title()} → Warehouse B → Kios Bandung → {destination.title()}"
        elif option_type == "cheapest":
            duration_hours = distance / 45  # 45 km/h average speed
            fuel_cost = distance * 10000  # IDR per km
            toll_cost = 25000
            co2 = distance * 0.4  # kg CO2 per km
            waypoints = [
                locations.get(origin, locations["plant-a"]),
                locations.get("warehouse-a", locations["warehouse-a"]),
                locations.get("kios-tasikmalaya", locations["kios-tasikmalaya"]),
                locations.get(destination, locations["kios-garut"])
            ]
            path = f"{origin.title()} → Warehouse A → Kios Tasikmalaya → {destination.title()}"
        else:  # greenest
            duration_hours = distance / 50  # 50 km/h average speed
            fuel_cost = distance * 11000  # IDR per km
            toll_cost = 35000
            co2 = distance * 0.3  # kg CO2 per km
            waypoints = [
                locations.get(origin, locations["plant-a"]),
                locations.get("warehouse-b", locations["warehouse-b"]),
                locations.get("kios-sumedang", locations["kios-sumedang"]),
                locations.get(destination, locations["kios-garut"])
            ]
            path = f"{origin.title()} → Warehouse B → Kios Sumedang → {destination.title()}"

        hours = int(duration_hours)
        minutes = int((duration_hours - hours) * 60)
        duration = f"{hours}h {minutes}min"

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
        """Get all locations from database, fallback to empty list if database unavailable."""
        if self.database is not None and is_database_available():
            try:
                locations = await Location.find().to_list()
                return locations
            except Exception as e:
                print(f"Database error getting locations: {e}")
                return []
        return []

    async def get_vehicles(self) -> List[Vehicle]:
        """Get all vehicles from database, fallback to mock data if database unavailable."""
        if self.database is not None and is_database_available():
            try:
                vehicles = await Vehicle.find().to_list()
                return vehicles
            except Exception as e:
                print(f"Database error getting vehicles: {e}")
                return await self._get_mock_vehicles()
        return await self._get_mock_vehicles()

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

    async def _get_mock_vehicles(self) -> List[Vehicle]:
        """Return mock vehicle data."""
        return [
            Vehicle(
                code="truck-small",
                name="Small Truck (3-5 tons)",
                min_capacity=3.0,
                max_capacity=5.0,
                fuel_consumption=2.8,
                average_speed=65.0,
                co2_factor=0.35,
                type="truck"
            ),
            Vehicle(
                code="truck-medium",
                name="Medium Truck (6-10 tons)",
                min_capacity=6.0,
                max_capacity=10.0,
                fuel_consumption=2.5,
                average_speed=60.0,
                co2_factor=0.4,
                type="truck"
            ),
            Vehicle(
                code="truck-large",
                name="Large Truck (11-15 tons)",
                min_capacity=11.0,
                max_capacity=15.0,
                fuel_consumption=2.2,
                average_speed=55.0,
                co2_factor=0.45,
                type="truck"
            )
        ]
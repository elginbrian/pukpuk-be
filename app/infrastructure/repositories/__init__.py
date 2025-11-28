from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities import ForecastData, Metrics, AIInsight, ChatSession, ChatMessage, RouteOptimizationRequest, RouteOptimizationResponse, RouteOption
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
        # Mock route optimization logic
        # In a real implementation, this would integrate with a routing service like Google Maps API, OSRM, etc.
        
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
        # Mock route generation logic
        if option_type == "fastest":
            duration_hours = distance / 60  # 60 km/h average speed
            fuel_cost = distance * 12000  # IDR per km
            toll_cost = 45000
            co2 = distance * 0.35  # kg CO2 per km
            path = f"{origin.title()} → Warehouse B → Kios Bandung → {destination.title()}"
        elif option_type == "cheapest":
            duration_hours = distance / 45  # 45 km/h average speed
            fuel_cost = distance * 10000  # IDR per km
            toll_cost = 25000
            co2 = distance * 0.4  # kg CO2 per km
            path = f"{origin.title()} → Warehouse A → Kios Tasikmalaya → {destination.title()}"
        else:  # greenest
            duration_hours = distance / 50  # 50 km/h average speed
            fuel_cost = distance * 11000  # IDR per km
            toll_cost = 35000
            co2 = distance * 0.3  # kg CO2 per km
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
            path=path
        )
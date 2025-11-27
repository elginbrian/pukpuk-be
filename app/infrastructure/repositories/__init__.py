from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities import ForecastData, Metrics, AIInsight, ChatSession, ChatMessage
from ...application.domain.interfaces import IForecastRepository, IMetricsRepository, IAIInsightsRepository, IChatSessionRepository
from ..database.database import is_database_available
import uuid
from datetime import datetime

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
        if self.database is None or not is_database_available():
           
            from datetime import datetime
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
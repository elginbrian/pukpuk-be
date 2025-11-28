from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities.ai_insight import AIInsight, ChatSession, ChatMessage
from ...application.domain.interfaces.ai_insight import IAIInsightsRepository, IChatSessionRepository
from ..database.database import is_database_available
import uuid
from datetime import datetime

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
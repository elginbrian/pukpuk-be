from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.ai_insight import AIInsight, ChatSession, ChatMessage

class IAIInsightsRepository(ABC):
    @abstractmethod
    async def save_insight(self, insight: AIInsight) -> None:
        pass

    @abstractmethod
    async def get_recent_insights(self, crop_type: str, region: str, season: str, limit: int = 10) -> List[AIInsight]:
        pass

class IChatSessionRepository(ABC):
    @abstractmethod
    async def create_session(self, crop_type: str, region: str, season: str) -> ChatSession:
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        pass

    @abstractmethod
    async def update_session_activity(self, session_id: str) -> None:
        pass

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> None:
        pass

    @abstractmethod
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        pass
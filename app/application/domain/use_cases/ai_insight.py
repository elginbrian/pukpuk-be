from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.ai_insight import AIInsightResponse, ChatSession, ChatMessage, AIInsight

class IGenerateAIInsightUseCase(ABC):
    @abstractmethod
    async def execute(self, query: str, crop_type: str, region: str, season: str, session_id: Optional[str] = None) -> AIInsightResponse:
        pass

    @abstractmethod
    async def get_recent_insights(self, limit: int = 10) -> List[AIInsight]:
        pass

    @abstractmethod
    async def generate_automatic_insights(self, crop_type: str, region: str, season: str, limit: int = 3) -> List[dict]:
        pass

class IChatSessionUseCase(ABC):
    @abstractmethod
    async def create_session(self, crop_type: str, region: str, season: str) -> ChatSession:
        pass

    @abstractmethod
    async def chat(self, session_id: str, message: str) -> tuple[str, List[str]]:
        pass

    @abstractmethod
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        pass
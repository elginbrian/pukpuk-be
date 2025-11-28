from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import ForecastData, Metrics, AIInsight, ChatSession, ChatMessage, RouteOptimizationResponse, RouteOptimizationRequest, Location, Vehicle, RouteConfiguration

class IForecastRepository(ABC):
    @abstractmethod
    async def get_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        pass

    @abstractmethod
    async def save_forecast_data(self, data: List[ForecastData]) -> None:
        pass

class IMetricsRepository(ABC):
    @abstractmethod
    async def get_latest_metrics(self, crop_type: str, region: str, season: str) -> Metrics:
        pass

    @abstractmethod
    async def save_metrics(self, metrics: Metrics) -> None:
        pass

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

class IRouteOptimizationRepository(ABC):
    @abstractmethod
    async def optimize_route(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        pass

    @abstractmethod
    async def get_locations(self) -> List[Location]:
        pass

    @abstractmethod
    async def get_vehicles(self) -> List[Vehicle]:
        pass

    @abstractmethod
    async def get_route_configurations(self) -> List[RouteConfiguration]:
        pass

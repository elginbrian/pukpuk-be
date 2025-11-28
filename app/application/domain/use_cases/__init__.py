from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import ForecastData, Metrics, AIInsightResponse, ChatSession, ChatMessage, RouteOptimizationResponse, RouteOptimizationRequest, Location

class IGetForecastUseCase(ABC):
    @abstractmethod
    async def execute(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        pass

class IGetMetricsUseCase(ABC):
    @abstractmethod
    async def execute(self, crop_type: str, region: str, season: str) -> Metrics:
        pass

class ISimulateScenarioUseCase(ABC):
    @abstractmethod
    async def execute(self, rainfall_change: float, crop_type: str = "rice", region: str = "jawa-barat", season: str = "wet-season") -> List[ForecastData]:
        pass

class IExportForecastUseCase(ABC):
    @abstractmethod
    async def execute(self, crop_type: str, region: str, season: str, format: str = "csv") -> str:
        pass

class IGenerateAIInsightUseCase(ABC):
    @abstractmethod
    async def execute(self, query: str, crop_type: str, region: str, season: str, session_id: Optional[str] = None) -> AIInsightResponse:
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

class IOptimizeRouteUseCase(ABC):
    @abstractmethod
    async def execute(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        pass

class IGetLocationsUseCase(ABC):
    @abstractmethod
    async def execute(self) -> List[Location]:
        pass

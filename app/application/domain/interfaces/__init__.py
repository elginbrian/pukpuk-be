from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import ForecastData, Metrics, AIInsight

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

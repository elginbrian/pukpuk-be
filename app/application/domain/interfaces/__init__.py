from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import ForecastData, Metrics

class IForecastRepository(ABC):
    @abstractmethod
    async def get_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        pass

    @abstractmethod
    async def save_forecast_data(self, data: List[ForecastData]) -> None:
        pass

class IMetricsRepository(ABC):
    @abstractmethod
    async def get_latest_metrics(self, crop_type: str, region: str, season: str) -> Optional[Metrics]:
        pass

    @abstractmethod
    async def save_metrics(self, metrics: Metrics) -> None:
        pass

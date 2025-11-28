from abc import ABC, abstractmethod
from typing import List
from ..entities.forecasting import ForecastData, Metrics

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
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities import ForecastData, Metrics
from ...application.domain.interfaces import IForecastRepository, IMetricsRepository
from ..database.database import is_database_available

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

    async def get_latest_metrics(self, crop_type: str, region: str, season: str) -> Optional[Metrics]:
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
        ).sort(-Metrics.id).first_or_none()
        
        return metrics

    async def save_metrics(self, metrics: Metrics) -> None:
        if self.database is not None and is_database_available():
            await metrics.insert()
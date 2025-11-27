from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from ...application.domain.entities import ForecastData, Metrics
from ...application.domain.interfaces import IForecastRepository, IMetricsRepository

class ForecastRepository(IForecastRepository):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database

    async def get_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        cursor = self.database.forecast_data.find({
            "crop_type": crop_type,
            "region": region,
            "season": season
        })
        return [ForecastData(**doc) async for doc in cursor]

    async def save_forecast_data(self, data: List[ForecastData]) -> None:
        if data:
            docs = [item.dict() for item in data]
            await self.database.forecast_data.insert_many(docs)

class MetricsRepository(IMetricsRepository):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database

    async def get_latest_metrics(self, crop_type: str, region: str, season: str) -> Optional[Metrics]:
        doc = await self.database.metrics.find_one({
            "crop_type": crop_type,
            "region": region,
            "season": season
        }, sort=[("_id", -1)])
        return Metrics(**doc) if doc else None

    async def save_metrics(self, metrics: Metrics) -> None:
        await self.database.metrics.insert_one(metrics.dict())
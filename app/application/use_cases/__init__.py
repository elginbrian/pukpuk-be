import random
from typing import List
from ..domain.entities import ForecastData, Metrics
from ..domain.use_cases import IGetForecastUseCase, IGetMetricsUseCase, ISimulateScenarioUseCase
from ..domain.interfaces import IForecastRepository, IMetricsRepository

class GetForecastUseCase(IGetForecastUseCase):
    def __init__(self, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository):
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo

    async def execute(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        # Get data from repository (will return empty list if database not available)
        data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        if data:
            return data

        # Generate and save data only if database is available
        from ...infrastructure.database.database import is_database_available
        if is_database_available():
            data = self._generate_forecast_data(crop_type, region, season)
            await self.forecast_repo.save_forecast_data(data)
        return data

    def _generate_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
        data = []
        base_demand = 4000 + random.randint(-500, 500)

        for i, month in enumerate(months):
            actual = base_demand + random.randint(-300, 300) if i < 6 else None
            predicted = base_demand + random.randint(-200, 400)
            data.append(ForecastData(
                month=month,
                actual=actual,
                predicted=predicted,
                crop_type=crop_type,
                region=region,
                season=season
            ))

        return data

class GetMetricsUseCase(IGetMetricsUseCase):
    def __init__(self, metrics_repo: IMetricsRepository):
        self.metrics_repo = metrics_repo

    async def execute(self, crop_type: str, region: str, season: str) -> Metrics:
        # Get metrics from repository (handles database availability)
        return await self.metrics_repo.get_latest_metrics(crop_type, region, season)

    def _generate_metrics(self, crop_type: str, region: str, season: str) -> Metrics:
        return Metrics(
            mae=142 + random.uniform(-20, 20),
            rmse=218 + random.uniform(-30, 30),
            demand_trend=15.3 + random.uniform(-5, 5),
            volatility_score=0.68 + random.uniform(-0.1, 0.1),
            crop_type=crop_type,
            region=region,
            season=season
        )

class SimulateScenarioUseCase(ISimulateScenarioUseCase):
    def __init__(self, forecast_repo: IForecastRepository):
        self.forecast_repo = forecast_repo

    async def execute(self, rainfall_change: float, crop_type: str = "rice", region: str = "jawa-barat", season: str = "wet-season") -> List[ForecastData]:
        # Get base forecast data
        data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        
        # If no data and database is available, generate base data
        from ...infrastructure.database.database import is_database_available
        if not data and is_database_available():
            # Generate base data
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
            data = []
            base_demand = 4000 + random.randint(-500, 500)
            for i, month in enumerate(months):
                actual = base_demand + random.randint(-300, 300) if i < 6 else None
                predicted = base_demand + random.randint(-200, 400)
                data.append(ForecastData(
                    month=month,
                    actual=actual,
                    predicted=predicted,
                    crop_type=crop_type,
                    region=region,
                    season=season
                ))
            await self.forecast_repo.save_forecast_data(data)

        # Apply rainfall change to predictions if we have data
        if data:
            for item in data:
                if item.predicted:
                    item.predicted *= (1 + rainfall_change / 100)

        return data
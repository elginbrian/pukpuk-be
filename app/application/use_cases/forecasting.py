import random
from typing import List, Optional
from ..domain.entities.forecasting import ForecastData, Metrics
from ..domain.use_cases.forecasting import IGetForecastUseCase, IGetMetricsUseCase, ISimulateScenarioUseCase
from ..domain.interfaces.forecasting import IForecastRepository, IMetricsRepository

class GetForecastUseCase(IGetForecastUseCase):
    def __init__(self, forecast_repo: IForecastRepository, metrics_repo: IMetricsRepository):
        self.forecast_repo = forecast_repo
        self.metrics_repo = metrics_repo

    async def execute(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        # Get data from repository (will return empty list if database not available)
        data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        if data:
           
            seen = set()
            deduped: List[ForecastData] = []
         
            month_order = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]) }
            for item in data:
                if item.month not in seen:
                    seen.add(item.month)
                    deduped.append(item)

            try:
                deduped.sort(key=lambda x: month_order.get(x.month, 999))
            except Exception:
                pass

            return deduped

        # Generate and save data only if database is available
        from ...infrastructure.database.database import is_database_available
        if is_database_available():
            data = self._generate_forecast_data(crop_type, region, season)
            await self.forecast_repo.save_forecast_data(data)
        return data

    def _generate_forecast_data(self, crop_type: str, region: str, season: str) -> List[ForecastData]:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
        
        # Get regency-specific patterns
        base_demands, regional_multiplier = self._get_regency_patterns(region, season)
        
        data = []
        
        for i, month in enumerate(months):
            base = base_demands[i] * regional_multiplier
            
            actual = base + random.randint(-200, 200) if i < 6 else None
            
            trend_factor = 1.05 if season == "wet-season" and i >= 6 else 0.98
            predicted = base * trend_factor + random.randint(-150, 250)
            
            ci_width = abs(predicted) * 0.15 
            upper_ci = predicted + ci_width
            lower_ci = max(0, predicted - ci_width)  
            
            data.append(ForecastData(
                month=month,
                actual=actual,
                predicted=max(0, predicted),  
                upper_ci=upper_ci,
                lower_ci=lower_ci,
                crop_type=crop_type,
                region=region,
                season=season
            ))

        return data

    def _get_regency_patterns(self, region: str, season: str) -> tuple[List[int], float]:
        """Get region-specific demand patterns and multipliers for East Java regencies."""
        region_lower = region.lower()
        
        # Base patterns for wet and dry seasons
        wet_base = [4500, 4800, 5200, 4000, 3800, 3600, 3500, 3400, 4200]
        dry_base = [3800, 3600, 3400, 3200, 3100, 3000, 2900, 2800, 3200]
        
        # Regency-specific adjustments
        regency_patterns = {
            "malang regency": {
                "multiplier": 1.15,  # Higher production due to fertile volcanic soil
                "wet_adjust": [500, 600, 700, 300, 200, 100, 0, -100, 400],  # Mountainous, irrigation dependent
                "dry_adjust": [200, 100, 0, -100, -200, -300, -400, -500, 0]
            },
            "blitar regency": {
                "multiplier": 1.25,  # Major rice producer
                "wet_adjust": [600, 700, 800, 400, 300, 200, 100, 0, 500],
                "dry_adjust": [300, 200, 100, 0, -100, -200, -300, -400, 100]
            },
            "kediri regency": {
                "multiplier": 1.20,  # Agricultural hub
                "wet_adjust": [550, 650, 750, 350, 250, 150, 50, -50, 450],
                "dry_adjust": [250, 150, 50, -50, -150, -250, -350, -450, 50]
            },
            "madiun regency": {
                "multiplier": 1.10,  # Mixed agriculture
                "wet_adjust": [450, 550, 650, 250, 150, 50, -50, -150, 350],
                "dry_adjust": [150, 50, -50, -150, -250, -350, -450, -550, -50]
            },
            "jember regency": {
                "multiplier": 1.05,  # Southern region, different climate
                "wet_adjust": [400, 500, 600, 200, 100, 0, -100, -200, 300],
                "dry_adjust": [100, 0, -100, -200, -300, -400, -500, -600, -100]
            }
        }
        
        if region_lower not in regency_patterns:
            base_demands = wet_base if season == "wet-season" else dry_base
            multiplier = 1.1
        else:
            pattern = regency_patterns[region_lower]
            base_pattern = wet_base if season == "wet-season" else dry_base
            adjustments = pattern["wet_adjust"] if season == "wet-season" else pattern["dry_adjust"]
            base_demands = [b + a for b, a in zip(base_pattern, adjustments)]
            multiplier = pattern["multiplier"]
        
        return base_demands, multiplier

class GetMetricsUseCase(IGetMetricsUseCase):
    def __init__(self, metrics_repo: IMetricsRepository):
        self.metrics_repo = metrics_repo

    async def execute(self, crop_type: str, region: str, season: str) -> Metrics:
        # Get metrics from repository (handles database availability)
        return await self.metrics_repo.get_latest_metrics(crop_type, region, season)

    def _generate_metrics(self, crop_type: str, region: str, season: str) -> Metrics:
        # More realistic metrics based on agricultural forecasting and crop characteristics
        crop_metrics = {
            "rice": {"mae": 85, "rmse": 135, "volatility": 0.45},
            "corn": {"mae": 120, "rmse": 200, "volatility": 0.65},
            "sugarcane": {"mae": 150, "rmse": 250, "volatility": 0.55},  # Sugarcane is perennial, more stable
            "soybean": {"mae": 110, "rmse": 180, "volatility": 0.70}
        }
        
        crop_data = crop_metrics.get(crop_type, crop_metrics["rice"])  # Default to rice metrics
        
        base_mae = crop_data["mae"]
        base_rmse = crop_data["rmse"]
        base_volatility = crop_data["volatility"]
        
        # Seasonal adjustments
        base_trend = 12.5 if season == "wet-season" else 8.3
        
        # Regional adjustments for regencies
        if "regency" in region.lower():
            base_mae *= 0.9
            base_rmse *= 0.9
            base_volatility *= 0.9
        
        return Metrics(
            mae=base_mae + random.uniform(-15, 25),
            rmse=base_rmse + random.uniform(-20, 35),
            demand_trend=base_trend + random.uniform(-3, 4),
            volatility_score=base_volatility + random.uniform(-0.08, 0.12),
            crop_type=crop_type,
            region=region,
            season=season
        )

class SimulateScenarioUseCase(ISimulateScenarioUseCase):
    def __init__(self, forecast_repo: IForecastRepository):
        self.forecast_repo = forecast_repo

    async def execute(self, rainfall_change: float, crop_type: str = "rice", region: str = "malang regency", season: str = "wet-season") -> List[ForecastData]:
        # Get base forecast data
        data = await self.forecast_repo.get_forecast_data(crop_type, region, season)
        
        # If no data and database is available, generate base data
        from ...infrastructure.database.database import is_database_available
        if not data and is_database_available():
            # Generate base data with regency-specific patterns
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
            
            base_demands, regional_multiplier = self._get_regency_patterns(region, season)
            
            data = []
            for i, month in enumerate(months):
                base = base_demands[i] * regional_multiplier
                
                actual = base + random.randint(-200, 200) if i < 6 else None
                trend_factor = 1.05 if season == "wet-season" and i >= 6 else 0.98
                predicted = base * trend_factor + random.randint(-150, 250)
                
                # Calculate confidence intervals
                ci_width = abs(predicted) * 0.15
                upper_ci = predicted + ci_width
                lower_ci = max(0, predicted - ci_width)
                
                data.append(ForecastData(
                    month=month,
                    actual=actual,
                    predicted=max(0, predicted),
                    upper_ci=upper_ci,
                    lower_ci=lower_ci,
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
                    ci_width = abs(item.predicted) * 0.15
                    item.upper_ci = item.predicted + ci_width
                    item.lower_ci = max(0, item.predicted - ci_width)

        return data
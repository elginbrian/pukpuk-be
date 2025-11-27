import asyncio
import random
from app.infrastructure.database.database import init_database, close_database
from app.infrastructure.repositories import ForecastRepository, MetricsRepository
from app.application.domain.entities import ForecastData, Metrics

async def seed_database():
    await init_database()

    # Get repositories
    from app.infrastructure.database.database import get_database
    db = await get_database()
    forecast_repo = ForecastRepository(db)
    metrics_repo = MetricsRepository(db)

    # Sample data for different crops, regions, seasons
    crops = ["rice", "corn", "wheat", "soybean"]
    regions = ["jawa-barat", "jawa-timur", "jawa-tengah", "sumatera-utara"]
    seasons = ["wet-season", "dry-season"]

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]

    for crop in crops:
        for region in regions:
            for season in seasons:
                # Generate forecast data
                forecast_data = []
                base_demand = 3000 + random.randint(-1000, 2000)

                for i, month in enumerate(months):
                    actual = base_demand + random.randint(-500, 500) if i < 6 else None
                    predicted = base_demand + random.randint(-300, 600)
                    forecast_data.append(ForecastData(
                        month=month,
                        actual=actual,
                        predicted=predicted,
                        crop_type=crop,
                        region=region,
                        season=season
                    ))

                await forecast_repo.save_forecast_data(forecast_data)

                # Generate metrics
                metrics = Metrics(
                    mae=120 + random.uniform(-30, 50),
                    rmse=200 + random.uniform(-40, 60),
                    demand_trend=10 + random.uniform(-10, 20),
                    volatility_score=0.5 + random.uniform(-0.2, 0.3),
                    crop_type=crop,
                    region=region,
                    season=season
                )

                await metrics_repo.save_metrics(metrics)

    print("Database seeded successfully!")

    await close_database()

if __name__ == "__main__":
    asyncio.run(seed_database())
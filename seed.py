import asyncio
import random
from app.infrastructure.database.database import init_database, close_database
from app.infrastructure.repositories import ForecastRepository, MetricsRepository
from app.application.domain.entities import ForecastData, Metrics, Location, Vehicle, RouteConfiguration

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

    # Seed locations
    locations = [
        Location(
            code="plant-a",
            name="Plant A - Karawang",
            coordinates=[-6.3045, 107.3035],
            type="plant",
            address="Jl. Industri No. 123, Karawang, Jawa Barat",
            icon_url="/icons/plant.png"
        ),
        Location(
            code="plant-b",
            name="Plant B - Gresik",
            coordinates=[-7.1539, 112.6543],
            type="plant",
            address="Jl. Produksi No. 456, Gresik, Jawa Timur",
            icon_url="/icons/plant.png"
        ),
        Location(
            code="warehouse-b",
            name="Warehouse B",
            coordinates=[-6.9175, 107.6191],
            type="warehouse",
            address="Jl. Gudang No. 789, Bandung, Jawa Barat",
            icon_url="/icons/warehouse.png"
        ),
        Location(
            code="kios-garut",
            name="Kios Garut",
            coordinates=[-7.2071, 107.9067],
            type="kiosk",
            address="Jl. Pasar No. 101, Garut, Jawa Barat",
            icon_url="/icons/kiosk.png"
        ),
        Location(
            code="kios-sukabumi",
            name="Kios Sukabumi",
            coordinates=[-6.9217, 106.9267],
            type="kiosk",
            address="Jl. Dagang No. 202, Sukabumi, Jawa Barat",
            icon_url="/icons/kiosk.png"
        ),
        Location(
            code="kios-cianjur",
            name="Kios Cianjur",
            coordinates=[-6.8225, 107.1394],
            type="kiosk",
            address="Jl. Toko No. 303, Cianjur, Jawa Barat",
            icon_url="/icons/kiosk.png"
        )
    ]

    for location in locations:
        await location.insert()

    # Seed vehicles
    vehicles = [
        Vehicle(
            code="truck-small",
            name="Small Truck (3-5 tons)",
            min_capacity=3.0,
            max_capacity=5.0,
            fuel_consumption=2.8,
            average_speed=65.0,
            co2_factor=0.35,
            type="truck"
        ),
        Vehicle(
            code="truck-medium",
            name="Medium Truck (6-10 tons)",
            min_capacity=6.0,
            max_capacity=10.0,
            fuel_consumption=2.5,
            average_speed=60.0,
            co2_factor=0.4,
            type="truck"
        ),
        Vehicle(
            code="truck-large",
            name="Large Truck (11-15 tons)",
            min_capacity=11.0,
            max_capacity=15.0,
            fuel_consumption=2.2,
            average_speed=55.0,
            co2_factor=0.45,
            type="truck"
        )
    ]

    for vehicle in vehicles:
        await vehicle.insert()

    # Seed route configurations (example configurations)
    route_configs = [
        RouteConfiguration(
            origin="plant-a",
            destination="kios-garut",
            vehicle_type="truck-medium",
            load_capacity=8.0,
            fastest_distance=150.0,
            cheapest_distance=160.0,
            greenest_distance=155.0,
            fastest_path=["plant-a", "warehouse-b", "kios-garut"],
            cheapest_path=["plant-a", "warehouse-b", "kios-garut"],
            greenest_path=["plant-a", "warehouse-b", "kios-garut"]
        ),
        RouteConfiguration(
            origin="plant-b",
            destination="kios-sukabumi",
            vehicle_type="truck-large",
            load_capacity=12.0,
            fastest_distance=200.0,
            cheapest_distance=210.0,
            greenest_distance=205.0,
            fastest_path=["plant-b", "warehouse-b", "kios-sukabumi"],
            cheapest_path=["plant-b", "warehouse-b", "kios-sukabumi"],
            greenest_path=["plant-b", "warehouse-b", "kios-sukabumi"]
        )
    ]

    for config in route_configs:
        await config.insert()

    print("Database seeded successfully!")

    await close_database()

if __name__ == "__main__":
    asyncio.run(seed_database())
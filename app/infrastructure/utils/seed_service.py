import asyncio
import random
import sys
import os
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path for standalone execution
if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ...application.domain.entities.forecasting import ForecastData, Metrics
from ...application.domain.entities.route_optimization import Location, Vehicle, RouteConfiguration
from ...infrastructure.repositories.forecasting import ForecastRepository, MetricsRepository
from ...infrastructure.repositories.route_optimization import RouteOptimizationRepository
from ...infrastructure.database.database import init_database, close_database, get_database

class SeedService:
    """Service for seeding database with initial data."""

    def __init__(self, database: AsyncIOMotorDatabase = None):
        self.database = database
        self.forecast_repo = ForecastRepository(database)
        self.metrics_repo = MetricsRepository(database)
        self.route_repo = RouteOptimizationRepository(database)

    async def seed_forecast_data(self) -> None:
        """Seed forecast data for different crops, regions, and seasons."""
        crops = ["rice", "corn", "wheat", "soybean"]
        regions = ["jawa-barat", "jawa-timur", "jawa-tengah", "sumatera-utara"]
        seasons = ["wet-season", "dry-season"]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]

        print("Seeding forecast data...")

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

                    await self.forecast_repo.save_forecast_data(forecast_data)

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

                    await self.metrics_repo.save_metrics(metrics)

        print("Forecast data seeded successfully!")

    async def seed_locations(self) -> None:
        """Seed the database with location data focused on East Java (Jawa Timur)."""
        locations_data = [
            # Plants - Pabrik
            {
                "code": "plant-surabaya",
                "name": "Plant Surabaya - Main Factory",
                "coordinates": [-7.2575, 112.7521],  # Surabaya coordinates
                "type": "plant",
                "address": "Jl. Industri No. 1, Surabaya, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png"
            },
            {
                "code": "plant-gresik",
                "name": "Plant Gresik - Secondary Factory",
                "coordinates": [-7.1539, 112.6543],  # Gresik coordinates
                "type": "plant",
                "address": "Jl. Produksi No. 45, Gresik, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png"
            },
            # Warehouses - Gudang
            {
                "code": "warehouse-surabaya",
                "name": "Warehouse Surabaya Central",
                "coordinates": [-7.2756, 112.6426],  # Surabaya warehouse area
                "type": "warehouse",
                "address": "Jl. Gudang No. 100, Surabaya, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png"
            },
            {
                "code": "warehouse-sidoarjo",
                "name": "Warehouse Sidoarjo",
                "coordinates": [-7.4558, 112.7183],  # Sidoarjo coordinates
                "type": "warehouse",
                "address": "Jl. Distribusi No. 25, Sidoarjo, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png"
            },
            {
                "code": "warehouse-malang",
                "name": "Warehouse Malang",
                "coordinates": [-7.9666, 112.6326],  # Malang coordinates
                "type": "warehouse",
                "address": "Jl. Logistik No. 50, Malang, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png"
            },
            # Kiosks - Kios di berbagai kota di Jawa Timur
            {
                "code": "kios-malang",
                "name": "Kiosk Malang",
                "coordinates": [-7.9666, 112.6326],
                "type": "kiosk",
                "address": "Jl. Raya No. 1, Malang, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            },
            {
                "code": "kios-blitar",
                "name": "Kiosk Blitar",
                "coordinates": [-8.0954, 112.1609],  # Blitar coordinates
                "type": "kiosk",
                "address": "Jl. Merdeka No. 15, Blitar, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            },
            {
                "code": "kios-kediri",
                "name": "Kiosk Kediri",
                "coordinates": [-7.8482, 112.0178],  # Kediri coordinates
                "type": "kiosk",
                "address": "Jl. Sudirman No. 30, Kediri, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            },
            {
                "code": "kios-madiun",
                "name": "Kiosk Madiun",
                "coordinates": [-7.6298, 111.5239],  # Madiun coordinates
                "type": "kiosk",
                "address": "Jl. Pahlawan No. 45, Madiun, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            },
            {
                "code": "kios-jember",
                "name": "Kiosk Jember",
                "coordinates": [-8.1845, 113.6681],  # Jember coordinates
                "type": "kiosk",
                "address": "Jl. Kalimantan No. 60, Jember, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            },
            {
                "code": "kios-batu",
                "name": "Kiosk Batu",
                "coordinates": [-7.8673, 112.5232],  # Batu coordinates
                "type": "kiosk",
                "address": "Jl. Panglima Sudirman No. 75, Batu, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            },
            {
                "code": "kios-probolinggo",
                "name": "Kiosk Probolinggo",
                "coordinates": [-7.7543, 113.2159],  # Probolinggo coordinates
                "type": "kiosk",
                "address": "Jl. Mastrip No. 90, Probolinggo, Jawa Timur",
                "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
            }
        ]

        print("Seeding locations (East Java focused)...")

        for location_data in locations_data:
            # Check if location already exists
            existing = await Location.find(Location.code == location_data["code"]).first_or_none()
            if existing:
                print(f"Location {location_data['code']} already exists, skipping...")
                continue

            location = Location(**location_data)
            await location.insert()
            print(f"Inserted location: {location.name}")

        print("Locations seeded successfully!")

    async def seed_vehicles(self) -> None:
        """Seed the database with vehicle data."""
        vehicles_data = [
            {
                "code": "truck-small",
                "name": "Small Truck (3-5 tons)",
                "min_capacity": 3.0,
                "max_capacity": 5.0,
                "fuel_consumption": 2.8,
                "average_speed": 65.0,
                "co2_factor": 0.35,
                "type": "truck"
            },
            {
                "code": "truck-medium",
                "name": "Medium Truck (6-10 tons)",
                "min_capacity": 6.0,
                "max_capacity": 10.0,
                "fuel_consumption": 2.5,
                "average_speed": 60.0,
                "co2_factor": 0.4,
                "type": "truck"
            },
            {
                "code": "truck-large",
                "name": "Large Truck (11-15 tons)",
                "min_capacity": 11.0,
                "max_capacity": 15.0,
                "fuel_consumption": 2.2,
                "average_speed": 55.0,
                "co2_factor": 0.45,
                "type": "truck"
            }
        ]

        print("Seeding vehicles...")

        for vehicle_data in vehicles_data:
            # Check if vehicle already exists
            existing = await Vehicle.find(Vehicle.code == vehicle_data["code"]).first_or_none()
            if existing:
                print(f"Vehicle {vehicle_data['code']} already exists, skipping...")
                continue

            vehicle = Vehicle(**vehicle_data)
            await vehicle.insert()
            print(f"Inserted vehicle: {vehicle.name}")

        print("Vehicles seeded successfully!")

    async def seed_route_configurations(self) -> None:
        """Seed the database with realistic route configuration data for East Java."""
        route_configs_data = [
            # Routes from plant-surabaya
            {
                "origin": "plant-surabaya",
                "destination": "kios-malang",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 95,  # Direct route ~95km
                "cheapest_distance": 105,  # Via warehouse ~105km
                "greenest_distance": 100,  # Balanced route ~100km
                "fastest_path": ["plant-surabaya", "kios-malang"],
                "cheapest_path": ["plant-surabaya", "warehouse-surabaya", "kios-malang"],
                "greenest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-malang"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-malang",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 95,
                "cheapest_distance": 105,
                "greenest_distance": 100,
                "fastest_path": ["plant-surabaya", "kios-malang"],
                "cheapest_path": ["plant-surabaya", "warehouse-surabaya", "kios-malang"],
                "greenest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-malang"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-malang",
                "vehicle_type": "truck-large",
                "load_capacity": 12.0,
                "fastest_distance": 95,
                "cheapest_distance": 105,
                "greenest_distance": 100,
                "fastest_path": ["plant-surabaya", "kios-malang"],
                "cheapest_path": ["plant-surabaya", "warehouse-surabaya", "kios-malang"],
                "greenest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-malang"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-blitar",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 170,  # Via toll road ~170km
                "cheapest_distance": 185,  # Regular road ~185km
                "greenest_distance": 175,  # Mixed route ~175km
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri", "kios-blitar"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-blitar",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 170,
                "cheapest_distance": 185,
                "greenest_distance": 175,
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri", "kios-blitar"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-jember",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 220,  # Main highway ~220km
                "cheapest_distance": 240,  # Alternative route ~240km
                "greenest_distance": 230,  # Scenic route ~230km
                "fastest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-probolinggo", "kios-jember"],
                "cheapest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar", "kios-jember"],
                "greenest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-jember"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-jember",
                "vehicle_type": "truck-large",
                "load_capacity": 12.0,
                "fastest_distance": 220,
                "cheapest_distance": 240,
                "greenest_distance": 230,
                "fastest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-probolinggo", "kios-jember"],
                "cheapest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar", "kios-jember"],
                "greenest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-jember"]
            },
            # Routes from plant-gresik
            {
                "origin": "plant-gresik",
                "destination": "kios-madiun",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 180,  # Direct route ~180km
                "cheapest_distance": 195,  # Via warehouse ~195km
                "greenest_distance": 185,  # Balanced route ~185km
                "fastest_path": ["plant-gresik", "warehouse-surabaya", "kios-madiun"],
                "cheapest_path": ["plant-gresik", "warehouse-sidoarjo", "kios-kediri", "kios-madiun"],
                "greenest_path": ["plant-gresik", "warehouse-surabaya", "kios-madiun"]
            },
            {
                "origin": "plant-gresik",
                "destination": "kios-batu",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 120,  # Mountain route ~120km
                "cheapest_distance": 135,  # Longer but cheaper ~135km
                "greenest_distance": 125,  # Efficient route ~125km
                "fastest_path": ["plant-gresik", "warehouse-malang", "kios-batu"],
                "cheapest_path": ["plant-gresik", "warehouse-sidoarjo", "warehouse-malang", "kios-batu"],
                "greenest_path": ["plant-gresik", "warehouse-malang", "kios-batu"]
            },
            # Routes from warehouse-surabaya
            {
                "origin": "warehouse-surabaya",
                "destination": "kios-probolinggo",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 110,  # Coastal route ~110km
                "cheapest_distance": 125,  # Inland route ~125km
                "greenest_distance": 115,  # Mixed route ~115km
                "fastest_path": ["warehouse-surabaya", "kios-probolinggo"],
                "cheapest_path": ["warehouse-surabaya", "warehouse-sidoarjo", "kios-probolinggo"],
                "greenest_path": ["warehouse-surabaya", "kios-probolinggo"]
            },
            # Routes from warehouse-malang
            {
                "origin": "warehouse-malang",
                "destination": "kios-blitar",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 75,  # Short route ~75km
                "cheapest_distance": 85,  # Alternative ~85km
                "greenest_distance": 78,  # Direct ~78km
                "fastest_path": ["warehouse-malang", "kios-blitar"],
                "cheapest_path": ["warehouse-malang", "kios-kediri", "kios-blitar"],
                "greenest_path": ["warehouse-malang", "kios-blitar"]
            },
            {
                "origin": "warehouse-malang",
                "destination": "kios-batu",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 25,  # Very close ~25km
                "cheapest_distance": 30,  # Local roads ~30km
                "greenest_distance": 26,  # Direct ~26km
                "fastest_path": ["warehouse-malang", "kios-batu"],
                "cheapest_path": ["warehouse-malang", "kios-batu"],
                "greenest_path": ["warehouse-malang", "kios-batu"]
            }
        ]

        print("Seeding route configurations (East Java focused)...")

        for config_data in route_configs_data:
            # Check if configuration already exists
            existing = await RouteConfiguration.find(
                RouteConfiguration.origin == config_data["origin"],
                RouteConfiguration.destination == config_data["destination"],
                RouteConfiguration.vehicle_type == config_data["vehicle_type"],
                RouteConfiguration.load_capacity == config_data["load_capacity"]
            ).first_or_none()

            if existing:
                print(f"Route config {config_data['origin']} -> {config_data['destination']} ({config_data['vehicle_type']}, {config_data['load_capacity']}t) already exists, skipping...")
                continue

            config = RouteConfiguration(**config_data)
            await config.insert()
            print(f"Inserted route config: {config.origin} -> {config.destination} ({config.vehicle_type}, {config.load_capacity}t)")

        print("Route configurations seeded successfully!")

    async def seed_all_data(self) -> None:
        """Seed all data types."""
        print("Starting complete data seeding...")

        await self.seed_forecast_data()
        await self.seed_locations()
        await self.seed_vehicles()
        await self.seed_route_configurations()

        print("Route configurations seeded successfully!")

    async def seed_all_data(self) -> None:
        """Seed all data types."""
        print("Starting complete data seeding...")

        await self.seed_forecast_data()
        await self.seed_locations()
        await self.seed_vehicles()
        await self.seed_route_configurations()

        print("All data seeding completed successfully!")

async def seed_database():
    """Standalone function to seed the database."""
    await init_database()

    # Get database instance
    db = await get_database()
    seed_service = SeedService(db)

    await seed_service.seed_all_data()

    await close_database()

if __name__ == "__main__":
    asyncio.run(seed_database())
import asyncio
import random
import sys
import os
import json
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
from ...application.domain.entities.maps import RegionMappings
from ...infrastructure.repositories.forecasting import ForecastRepository, MetricsRepository
from ...infrastructure.repositories.route_optimization import RouteOptimizationRepository
from ...infrastructure.repositories.maps import MapsRepository
from ...infrastructure.database.database import init_database, close_database, get_database_sync

class SeedService:
    """Service for seeding database with initial data."""

    def __init__(self, database: AsyncIOMotorDatabase = None):
        self.database = database
        self.forecast_repo = ForecastRepository(database)
        self.metrics_repo = MetricsRepository(database)
        self.route_repo = RouteOptimizationRepository(database)
        self.maps_repo = MapsRepository(database)

    async def seed_forecast_data(self) -> None:
        """Seed forecast data for different crops, regions, and seasons."""
        crops = ["rice", "corn", "sugarcane", "soybean"]
        regions = ["malang regency", "blitar regency", "kediri regency", "madiun regency", "jember regency"]
        seasons = ["wet-season", "dry-season"]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]

        print("Seeding forecast data...")

        for crop in crops:
            for region in regions:
                for season in seasons:
                    # Generate forecast data with regency-specific patterns
                    forecast_data = []
                    
                    # Get regency-specific base patterns
                    base_demands, multiplier = self._get_seed_regency_patterns(region, season)
                    
                    for i, month in enumerate(months):
                        base = base_demands[i] * multiplier
                        actual = base + random.randint(-200, 200) if i < 6 else None
                        predicted = base + random.randint(-150, 250)
                        
                        ci_width = abs(predicted) * 0.15
                        upper_ci = predicted + ci_width
                        lower_ci = max(0, predicted - ci_width)
                        
                        forecast_data.append(ForecastData(
                            month=month,
                            actual=actual,
                            predicted=max(0, predicted),
                            upper_ci=upper_ci,
                            lower_ci=lower_ci,
                            crop_type=crop,
                            region=region,
                            season=season
                        ))

                    await self.forecast_repo.save_forecast_data(forecast_data)

                    # Generate metrics with crop-specific characteristics
                    crop_metrics = {
                        "rice": {"mae": 120, "rmse": 200, "volatility": 0.5},
                        "corn": {"mae": 150, "rmse": 250, "volatility": 0.65},
                        "sugarcane": {"mae": 180, "rmse": 300, "volatility": 0.55},
                        "soybean": {"mae": 140, "rmse": 230, "volatility": 0.70}
                    }
                    
                    crop_data = crop_metrics.get(crop, crop_metrics["rice"])
                    base_mae = crop_data["mae"]
                    base_rmse = crop_data["rmse"]
                    base_volatility = crop_data["volatility"]
                    
                    # Regional adjustment for regencies
                    if "regency" in region.lower():
                        base_mae *= 0.9
                        base_rmse *= 0.9
                        base_volatility *= 0.9
                    
                    metrics = Metrics(
                        mae=base_mae + random.uniform(-30, 50),
                        rmse=base_rmse + random.uniform(-40, 60),
                        demand_trend=10 + random.uniform(-10, 20),
                        volatility_score=base_volatility + random.uniform(-0.2, 0.3),
                        crop_type=crop,
                        region=region,
                        season=season
                    )

                    await self.metrics_repo.save_metrics(metrics)

        print("Forecast data seeded successfully!")

    def _get_seed_regency_patterns(self, region: str, season: str) -> tuple[list[int], float]:
        """Get region-specific demand patterns and multipliers for East Java regencies (for seeding)."""
        region_lower = region.lower()
        
        # Base patterns for wet and dry seasons
        wet_base = [4500, 4800, 5200, 4000, 3800, 3600, 3500, 3400, 4200]
        dry_base = [3800, 3600, 3400, 3200, 3100, 3000, 2900, 2800, 3200]
        
        # Regency-specific adjustments (simplified for seeding)
        regency_patterns = {
            "malang regency": {
                "multiplier": 1.15,
                "wet_adjust": [500, 600, 700, 300, 200, 100, 0, -100, 400],
                "dry_adjust": [200, 100, 0, -100, -200, -300, -400, -500, 0]
            },
            "blitar regency": {
                "multiplier": 1.25,
                "wet_adjust": [600, 700, 800, 400, 300, 200, 100, 0, 500],
                "dry_adjust": [300, 200, 100, 0, -100, -200, -300, -400, 100]
            },
            "kediri regency": {
                "multiplier": 1.20,
                "wet_adjust": [550, 650, 750, 350, 250, 150, 50, -50, 450],
                "dry_adjust": [250, 150, 50, -50, -150, -250, -350, -450, 50]
            },
            "madiun regency": {
                "multiplier": 1.10,
                "wet_adjust": [450, 550, 650, 250, 150, 50, -50, -150, 350],
                "dry_adjust": [150, 50, -50, -150, -250, -350, -450, -550, -50]
            },
            "jember regency": {
                "multiplier": 1.05,
                "wet_adjust": [400, 500, 600, 200, 100, 0, -100, -200, 300],
                "dry_adjust": [100, 0, -100, -200, -300, -400, -500, -600, -100]
            }
        }
        
        # Default pattern for unknown regencies
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

    async def seed_locations(self) -> None:
        """Seed the database with location data focused on East Java (Jawa Timur)."""
        data_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'locations.json')
        with open(data_file, 'r') as f:
            locations_data = json.load(f)

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
        data_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'vehicles.json')
        with open(data_file, 'r') as f:
            vehicles_data = json.load(f)

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
        """Seed the database with comprehensive route configuration data for East Java."""
        data_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'route_configurations.json')
        with open(data_file, 'r') as f:
            route_configs_data = json.load(f)

        print("Seeding route configurations...")

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

    async def seed_region_mappings(self) -> None:
        """Seed the database with region to geojson filename mappings."""
        print("Seeding region mappings...")

        # Check if already seeded
        existing = await RegionMappings.find().first_or_none()
        if existing:
            print("Region mappings already exist, skipping...")
            return

        data_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'region_mappings.json')
        with open(data_file, 'r') as f:
            mappings = json.load(f)

        region_mappings = RegionMappings(mappings=mappings)
        await region_mappings.insert()
        print("Region mappings seeded successfully!")

    async def seed_all_data(self) -> None:
        """Seed all data types."""
        print("Starting complete data seeding...")

        await self.seed_forecast_data()
        await self.seed_locations()
        await self.seed_vehicles()
        await self.seed_route_configurations()
        await self.seed_region_mappings()

        print("All data seeding completed successfully!")

async def seed_database():
    """Standalone function to seed the database."""
    await init_database()

    # Get database instance
    db = get_database_sync()
    seed_service = SeedService(db)

    await seed_service.seed_all_data()

    await close_database()

if __name__ == "__main__":
    asyncio.run(seed_database())
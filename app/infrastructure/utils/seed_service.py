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
from ...infrastructure.database.database import init_database, close_database, get_database_sync

class SeedService:
    """Service for seeding database with initial data."""

    def __init__(self, database: AsyncIOMotorDatabase = None):
        self.database = database
        self.forecast_repo = ForecastRepository(database)
        self.metrics_repo = MetricsRepository(database)
        self.route_repo = RouteOptimizationRepository(database)

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
        """Seed the database with comprehensive route configuration data for East Java."""
        route_configs_data = [
            # Routes from plant-surabaya to all destinations
            {
                "origin": "plant-surabaya",
                "destination": "kios-malang",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
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
                "fastest_distance": 170,
                "cheapest_distance": 185,
                "greenest_distance": 175,
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
                "destination": "kios-blitar",
                "vehicle_type": "truck-large",
                "load_capacity": 12.0,
                "fastest_distance": 170,
                "cheapest_distance": 185,
                "greenest_distance": 175,
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri", "kios-blitar"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-kediri",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 140,
                "cheapest_distance": 155,
                "greenest_distance": 145,
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-kediri"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-kediri"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-kediri",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 140,
                "cheapest_distance": 155,
                "greenest_distance": 145,
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-kediri"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-kediri"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-madiun",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 200,
                "cheapest_distance": 220,
                "greenest_distance": 205,
                "fastest_path": ["plant-surabaya", "warehouse-surabaya", "kios-madiun"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri", "kios-madiun"],
                "greenest_path": ["plant-surabaya", "warehouse-surabaya", "kios-madiun"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-madiun",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 200,
                "cheapest_distance": 220,
                "greenest_distance": 205,
                "fastest_path": ["plant-surabaya", "warehouse-surabaya", "kios-madiun"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-kediri", "kios-madiun"],
                "greenest_path": ["plant-surabaya", "warehouse-surabaya", "kios-madiun"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-jember",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 220,
                "cheapest_distance": 240,
                "greenest_distance": 230,
                "fastest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-probolinggo", "kios-jember"],
                "cheapest_path": ["plant-surabaya", "warehouse-malang", "kios-blitar", "kios-jember"],
                "greenest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-jember"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-jember",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 220,
                "cheapest_distance": 240,
                "greenest_distance": 230,
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
            {
                "origin": "plant-surabaya",
                "destination": "kios-batu",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 110,
                "cheapest_distance": 125,
                "greenest_distance": 115,
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-batu"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "warehouse-malang", "kios-batu"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-batu"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-batu",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 110,
                "cheapest_distance": 125,
                "greenest_distance": 115,
                "fastest_path": ["plant-surabaya", "warehouse-malang", "kios-batu"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "warehouse-malang", "kios-batu"],
                "greenest_path": ["plant-surabaya", "warehouse-malang", "kios-batu"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-probolinggo",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 100,
                "cheapest_distance": 115,
                "greenest_distance": 105,
                "fastest_path": ["plant-surabaya", "kios-probolinggo"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-probolinggo"],
                "greenest_path": ["plant-surabaya", "kios-probolinggo"]
            },
            {
                "origin": "plant-surabaya",
                "destination": "kios-probolinggo",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 100,
                "cheapest_distance": 115,
                "greenest_distance": 105,
                "fastest_path": ["plant-surabaya", "kios-probolinggo"],
                "cheapest_path": ["plant-surabaya", "warehouse-sidoarjo", "kios-probolinggo"],
                "greenest_path": ["plant-surabaya", "kios-probolinggo"]
            },

            # Routes from plant-gresik
            {
                "origin": "plant-gresik",
                "destination": "kios-malang",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 100,
                "cheapest_distance": 115,
                "greenest_distance": 105,
                "fastest_path": ["plant-gresik", "warehouse-surabaya", "kios-malang"],
                "cheapest_path": ["plant-gresik", "warehouse-sidoarjo", "kios-malang"],
                "greenest_path": ["plant-gresik", "warehouse-surabaya", "kios-malang"]
            },
            {
                "origin": "plant-gresik",
                "destination": "kios-malang",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 100,
                "cheapest_distance": 115,
                "greenest_distance": 105,
                "fastest_path": ["plant-gresik", "warehouse-surabaya", "kios-malang"],
                "cheapest_path": ["plant-gresik", "warehouse-sidoarjo", "kios-malang"],
                "greenest_path": ["plant-gresik", "warehouse-surabaya", "kios-malang"]
            },
            {
                "origin": "plant-gresik",
                "destination": "kios-madiun",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 180,
                "cheapest_distance": 195,
                "greenest_distance": 185,
                "fastest_path": ["plant-gresik", "warehouse-surabaya", "kios-madiun"],
                "cheapest_path": ["plant-gresik", "warehouse-sidoarjo", "kios-kediri", "kios-madiun"],
                "greenest_path": ["plant-gresik", "warehouse-surabaya", "kios-madiun"]
            },
            {
                "origin": "plant-gresik",
                "destination": "kios-batu",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 120,
                "cheapest_distance": 135,
                "greenest_distance": 125,
                "fastest_path": ["plant-gresik", "warehouse-malang", "kios-batu"],
                "cheapest_path": ["plant-gresik", "warehouse-sidoarjo", "warehouse-malang", "kios-batu"],
                "greenest_path": ["plant-gresik", "warehouse-malang", "kios-batu"]
            },

            # Routes from warehouses
            {
                "origin": "warehouse-surabaya",
                "destination": "kios-malang",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 90,
                "cheapest_distance": 100,
                "greenest_distance": 95,
                "fastest_path": ["warehouse-surabaya", "kios-malang"],
                "cheapest_path": ["warehouse-surabaya", "warehouse-sidoarjo", "kios-malang"],
                "greenest_path": ["warehouse-surabaya", "kios-malang"]
            },
            {
                "origin": "warehouse-surabaya",
                "destination": "kios-probolinggo",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 110,
                "cheapest_distance": 125,
                "greenest_distance": 115,
                "fastest_path": ["warehouse-surabaya", "kios-probolinggo"],
                "cheapest_path": ["warehouse-surabaya", "warehouse-sidoarjo", "kios-probolinggo"],
                "greenest_path": ["warehouse-surabaya", "kios-probolinggo"]
            },
            {
                "origin": "warehouse-malang",
                "destination": "kios-blitar",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 75,
                "cheapest_distance": 85,
                "greenest_distance": 78,
                "fastest_path": ["warehouse-malang", "kios-blitar"],
                "cheapest_path": ["warehouse-malang", "kios-kediri", "kios-blitar"],
                "greenest_path": ["warehouse-malang", "kios-blitar"]
            },
            {
                "origin": "warehouse-malang",
                "destination": "kios-batu",
                "vehicle_type": "truck-small",
                "load_capacity": 4.0,
                "fastest_distance": 25,
                "cheapest_distance": 30,
                "greenest_distance": 26,
                "fastest_path": ["warehouse-malang", "kios-batu"],
                "cheapest_path": ["warehouse-malang", "kios-batu"],
                "greenest_path": ["warehouse-malang", "kios-batu"]
            },
            {
                "origin": "warehouse-sidoarjo",
                "destination": "kios-malang",
                "vehicle_type": "truck-medium",
                "load_capacity": 8.0,
                "fastest_distance": 85,
                "cheapest_distance": 95,
                "greenest_distance": 88,
                "fastest_path": ["warehouse-sidoarjo", "kios-malang"],
                "cheapest_path": ["warehouse-sidoarjo", "warehouse-malang", "kios-malang"],
                "greenest_path": ["warehouse-sidoarjo", "kios-malang"]
            }
        ]

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
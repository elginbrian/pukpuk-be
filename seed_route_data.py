#!/usr/bin/env python3
"""
Route Data Seeding Script

This script seeds the MongoDB database with initial route optimization data
including locations and route configurations for the PukPuk application.
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.application.domain.entities import Location, RouteConfiguration

# Load environment variables
load_dotenv()

async def seed_locations():
    """Seed the database with location data."""
    locations_data = [
        {
            "code": "plant-a",
            "name": "Plant A - Karawang",
            "coordinates": [-6.3074, 107.3103],
            "type": "plant",
            "address": "Jl. Industri No. 123, Karawang, Jawa Barat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png"
        },
        {
            "code": "plant-b",
            "name": "Plant B - Surabaya",
            "coordinates": [-7.1612, 112.6535],
            "type": "plant",
            "address": "Jl. Produksi No. 456, Surabaya, Jawa Timur",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png"
        },
        {
            "code": "warehouse-a",
            "name": "Warehouse A - Jakarta",
            "coordinates": [-6.2088, 106.8166],
            "type": "warehouse",
            "address": "Jl. Gudang No. 789, Jakarta Pusat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png"
        },
        {
            "code": "warehouse-b",
            "name": "Warehouse B - Cirebon",
            "coordinates": [-6.595, 106.8166],
            "type": "warehouse",
            "address": "Jl. Distribusi No. 101, Cirebon, Jawa Barat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png"
        },
        {
            "code": "kios-bandung",
            "name": "Kiosk Bandung",
            "coordinates": [-6.9175, 107.6191],
            "type": "kiosk",
            "address": "Jl. Raya No. 202, Bandung, Jawa Barat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
        },
        {
            "code": "kios-tasikmalaya",
            "name": "Kiosk Tasikmalaya",
            "coordinates": [-7.3156, 108.2048],
            "type": "kiosk",
            "address": "Jl. Pasar No. 303, Tasikmalaya, Jawa Barat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
        },
        {
            "code": "kios-sumedang",
            "name": "Kiosk Sumedang",
            "coordinates": [-6.9858, 107.8148],
            "type": "kiosk",
            "address": "Jl. Sentral No. 404, Sumedang, Jawa Barat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
        },
        {
            "code": "kios-garut",
            "name": "Kiosk Garut",
            "coordinates": [-7.207, 107.9177],
            "type": "kiosk",
            "address": "Jl. Utama No. 505, Garut, Jawa Barat",
            "icon_url": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
        }
    ]

    # Insert locations
    for location_data in locations_data:
        # Check if location already exists
        existing = await Location.find(Location.code == location_data["code"]).first_or_none()
        if existing:
            print(f"Location {location_data['code']} already exists, skipping...")
            continue

        location = Location(**location_data)
        await location.insert()
        print(f"Inserted location: {location.name}")

async def seed_route_configurations():
    """Seed the database with route configuration data."""
    route_configs_data = [
        # Routes from plant-a
        {
            "origin": "plant-a",
            "destination": "kios-garut",
            "vehicle_type": "truck-small",
            "load_capacity": 5.0,
            "fastest_distance": 245,
            "cheapest_distance": 280,
            "greenest_distance": 260,
            "fastest_path": ["plant-a", "warehouse-b", "kios-bandung", "kios-garut"],
            "cheapest_path": ["plant-a", "warehouse-a", "kios-tasikmalaya", "kios-garut"],
            "greenest_path": ["plant-a", "warehouse-b", "kios-sumedang", "kios-garut"]
        },
        {
            "origin": "plant-a",
            "destination": "kios-bandung",
            "vehicle_type": "truck-small",
            "load_capacity": 5.0,
            "fastest_distance": 180,
            "cheapest_distance": 220,
            "greenest_distance": 200,
            "fastest_path": ["plant-a", "warehouse-b", "kios-bandung"],
            "cheapest_path": ["plant-a", "warehouse-a", "kios-bandung"],
            "greenest_path": ["plant-a", "warehouse-b", "kios-bandung"]
        },
        {
            "origin": "plant-a",
            "destination": "kios-tasikmalaya",
            "vehicle_type": "truck-small",
            "load_capacity": 5.0,
            "fastest_distance": 150,
            "cheapest_distance": 190,
            "greenest_distance": 170,
            "fastest_path": ["plant-a", "warehouse-b", "kios-tasikmalaya"],
            "cheapest_path": ["plant-a", "warehouse-a", "kios-tasikmalaya"],
            "greenest_path": ["plant-a", "warehouse-b", "kios-tasikmalaya"]
        },
        {
            "origin": "plant-a",
            "destination": "kios-sumedang",
            "vehicle_type": "truck-small",
            "load_capacity": 5.0,
            "fastest_distance": 120,
            "cheapest_distance": 160,
            "greenest_distance": 140,
            "fastest_path": ["plant-a", "warehouse-b", "kios-sumedang"],
            "cheapest_path": ["plant-a", "warehouse-a", "kios-sumedang"],
            "greenest_path": ["plant-a", "warehouse-b", "kios-sumedang"]
        },
        # Add configurations for different vehicle types and load capacities
        {
            "origin": "plant-a",
            "destination": "kios-garut",
            "vehicle_type": "truck-medium",
            "load_capacity": 10.0,
            "fastest_distance": 245,
            "cheapest_distance": 280,
            "greenest_distance": 260,
            "fastest_path": ["plant-a", "warehouse-b", "kios-bandung", "kios-garut"],
            "cheapest_path": ["plant-a", "warehouse-a", "kios-tasikmalaya", "kios-garut"],
            "greenest_path": ["plant-a", "warehouse-b", "kios-sumedang", "kios-garut"]
        },
        {
            "origin": "plant-a",
            "destination": "kios-garut",
            "vehicle_type": "truck-large",
            "load_capacity": 15.0,
            "fastest_distance": 245,
            "cheapest_distance": 280,
            "greenest_distance": 260,
            "fastest_path": ["plant-a", "warehouse-b", "kios-bandung", "kios-garut"],
            "cheapest_path": ["plant-a", "warehouse-a", "kios-tasikmalaya", "kios-garut"],
            "greenest_path": ["plant-a", "warehouse-b", "kios-sumedang", "kios-garut"]
        }
    ]

    # Insert route configurations
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

async def main():
    """Main seeding function."""
    # Get MongoDB connection string from environment
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/pukpuk")

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        database = client.get_database("pukpuk")

        # Initialize Beanie with the database
        await init_beanie(database, document_models=[Location, RouteConfiguration])

        print("Connected to MongoDB successfully!")
        print("Starting data seeding...")

        # Seed locations
        print("\nSeeding locations...")
        await seed_locations()

        # Seed route configurations
        print("\nSeeding route configurations...")
        await seed_route_configurations()

        print("\nData seeding completed successfully!")

    except Exception as e:
        print(f"Error during seeding: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
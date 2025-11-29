#!/usr/bin/env python3
"""
Database Seeding Script

This script seeds the MongoDB database with all initial data for the PukPuk application
including forecast data, locations, vehicles, and route configurations.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.infrastructure.database.database import init_database, close_database, get_database
from app.infrastructure.utils.seed_service import SeedService

async def main():
    """Main seeding function."""
    try:
        print("Starting complete database seeding...")

        await init_database()

        # Get database instance
        db = get_database()
        seed_service = SeedService(db)

        # Seed all data types
        await seed_service.seed_forecast_data()
        await seed_service.seed_locations()
        await seed_service.seed_vehicles()
        await seed_service.seed_route_configurations()

        print("\nComplete database seeding completed successfully!")

        await close_database()

    except Exception as e:
        print(f"Error during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
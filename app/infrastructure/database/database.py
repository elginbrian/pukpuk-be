from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from ...infrastructure.config.settings import settings
from ...application.domain.entities import ForecastData, Metrics, AIInsight, ChatSession, ChatMessage, Location, Vehicle, RouteConfiguration
import random
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
database: AsyncIOMotorDatabase = None
db_available = False

async def init_database():
    global client, database, db_available
    try:
        client = AsyncIOMotorClient(settings.database_url, serverSelectionTimeoutMS=5000)
        database = client[settings.database_name]
        # Test connection
        await client.admin.command('ping')
        await init_beanie(database, document_models=[ForecastData, Metrics, AIInsight, ChatSession, ChatMessage, Location, Vehicle, RouteConfiguration])
        db_available = True
        logger.info("Database connected successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Using mock data mode.")
        db_available = False

def get_database() -> AsyncIOMotorDatabase:
    """Get database synchronously - assumes database is already initialized"""
    if not db_available or database is None:
        raise RuntimeError("Database not available")
    return database

def is_database_available() -> bool:
    return db_available

async def seed_database():
    """Seed the database with initial data"""
    if not db_available:
        print("Database not available, skipping seeding")
        return

    # Check if data already exists
    existing_forecast = await ForecastData.find().first_or_none()
    if existing_forecast:
        print("Database already seeded")
        return

    print("Seeding database...")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    forecast_data = []
    base_demand = 4000

    for i, month in enumerate(months):
        actual = base_demand + random.randint(-300, 300) if i < 6 else None
        predicted = base_demand + random.randint(-200, 400)
        forecast_data.append(ForecastData(
            month=month,
            actual=actual,
            predicted=predicted,
            crop_type="rice",
            region="jawa-barat",
            season="wet-season"
        ))

    await ForecastData.insert_many(forecast_data)

    # Seed metrics
    metrics = Metrics(
        mae=142.0,
        rmse=218.0,
        demand_trend=15.3,
        volatility_score=0.68,
        crop_type="rice",
        region="jawa-barat",
        season="wet-season"
    )
    await metrics.insert()

    print("Database seeded successfully")

async def close_database():
    if client:
        client.close()
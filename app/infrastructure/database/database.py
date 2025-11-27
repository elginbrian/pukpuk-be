from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from ...infrastructure.config.settings import settings
from ...application.domain.entities import ForecastData, Metrics

client: AsyncIOMotorClient = None
database = None

async def init_database():
    global client, database
    client = AsyncIOMotorClient(settings.database_url)
    database = client[settings.database_name]
    await init_beanie(database, document_models=[ForecastData, Metrics])

async def get_database():
    return database

async def close_database():
    if client:
        client.close()
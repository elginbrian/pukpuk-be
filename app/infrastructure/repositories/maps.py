from motor.motor_asyncio import AsyncIOMotorDatabase
from ...application.domain.entities.maps import RegionMappings

class MapsRepository:
    """Repository for maps-related operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database

    async def get_region_mappings(self) -> dict:
        """Get the region to geojson filename mappings."""
        mappings_doc = await RegionMappings.find().first_or_none()
        if mappings_doc:
            return mappings_doc.mappings
        return {}
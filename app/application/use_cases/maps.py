from ...infrastructure.repositories.maps import MapsRepository

class MapsUseCase:
    """Use case for maps operations."""

    def __init__(self, maps_repo: MapsRepository):
        self.maps_repo = maps_repo

    async def get_region_mappings(self) -> dict:
        """Get region to geojson filename mappings."""
        return await self.maps_repo.get_region_mappings()
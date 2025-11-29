from ..domain.interfaces.demand_heatmap import IDemandHeatmapRepository
from ..domain.entities.demand_heatmap import DemandHeatmapData

class GetDemandHeatmapDataUseCase:
    """Use case for getting demand heatmap data."""

    def __init__(self, demand_heatmap_repo: IDemandHeatmapRepository):
        self.demand_heatmap_repo = demand_heatmap_repo

    async def execute(self, level: str, mode: str, layer: str) -> DemandHeatmapData:
        """Get demand heatmap data for the specified parameters."""
        map_analytics, regional_insights = await self.demand_heatmap_repo.get_demand_heatmap_data(level, mode, layer)

        return DemandHeatmapData(
            mapAnalytics=map_analytics,
            regionalInsights=regional_insights
        )
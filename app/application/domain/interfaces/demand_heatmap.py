from abc import ABC, abstractmethod
from typing import Dict, List
from ..entities.demand_heatmap import MapAnalyticsData, RegionalInsight

class IDemandHeatmapRepository(ABC):
    @abstractmethod
    async def get_demand_heatmap_data(self, level: str, mode: str, layer: str) -> tuple[Dict[str, MapAnalyticsData], List[RegionalInsight]]:
        """Get demand heatmap data including map analytics and regional insights."""
        pass
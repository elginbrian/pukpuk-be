from pydantic import BaseModel
from typing import Dict, List

class MapAnalyticsData(BaseModel):
    status: str  # "critical" | "warning" | "safe" | "overstock" | "unknown"
    value: float
    label: str

class RegionalInsight(BaseModel):
    name: str
    demand: str
    confidence: int
    trend: str  # "up" | "down" | "stable"
    risk: str   # "low" | "medium" | "high"

class DemandHeatmapData(BaseModel):
    mapAnalytics: Dict[str, MapAnalyticsData]
    regionalInsights: List[RegionalInsight]
import json
import os
import random
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...application.domain.interfaces.demand_heatmap import IDemandHeatmapRepository
from ...application.domain.entities.demand_heatmap import MapAnalyticsData, RegionalInsight
from .maps import MapsRepository

class DemandHeatmapRepository(IDemandHeatmapRepository):
    """Repository for demand heatmap operations."""

    def __init__(self, database: AsyncIOMotorDatabase, maps_repo: MapsRepository):
        self.database = database
        self.maps_repo = maps_repo

    async def get_demand_heatmap_data(self, level: str, mode: str, layer: str) -> tuple[Dict[str, MapAnalyticsData], List[RegionalInsight]]:
        """Get demand heatmap data including map analytics and regional insights."""

        # Get region mappings to determine which geojson file to use
        region_mappings = await self.maps_repo.get_region_mappings()

        # Determine which geojson file to read based on level
        filename = region_mappings.get(level, "indonesia")
        if not filename:
            if level == "pulau" or level == "indonesia":
                filename = "indonesia"
            else:
                filename = "kabupaten"  # Default fallback

        # Load geojson data to get actual region codes
        geojson_path = os.path.join("data", "maps", f"{filename}.geojson")
        region_codes = []

        if os.path.exists(geojson_path):
            try:
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)

                # Extract region codes from geojson features
                for feature in geojson_data.get('features', []):
                    props = feature.get('properties', {})
                    # Try different possible ID fields
                    region_id = (
                        props.get('prov_id') or
                        props.get('regency_code', '').replace('id', '') or
                        props.get('district_code', '').replace('id', '') or
                        props.get('ID') or
                        props.get('id') or
                        props.get('KODE') or
                        props.get('kode') or
                        props.get('bps_code')
                    )
                    if region_id:
                        region_codes.append(str(region_id))
            except Exception as e:
                print(f"Error reading geojson {geojson_path}: {e}")

        # If no regions found in geojson, use fallback region codes
        if not region_codes:
            region_codes = (
                ["11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "31", "32", "33", "34", "35", "36", "51", "52", "53", "61", "62", "63", "64", "65", "71", "72", "73", "74", "75", "76", "81", "82", "91", "94"]
                if level == "pulau"
                else ["3501", "3502", "3507", "3573", "3578", "3204", "3273", "1101", "1102", "1103", "1104", "1105", "1106", "1107", "1108", "1171"]
            )

        # Generate map analytics data
        map_analytics = {}
        for region_code in region_codes:
            # Generate realistic demand values (50-1000 tons)
            base_value = random.randint(50, 1000)

            # Apply some logic based on mode and layer
            if mode == "forecast":
                # Add some forecast-specific logic
                risk_factor = random.random()
                if risk_factor < 0.15:
                    status = "critical"
                    label = "Defisit (Urgent)"
                    # Critical regions have lower values
                    value = base_value * 0.3
                elif risk_factor < 0.35:
                    status = "warning"
                    label = "Menipis (Waspada)"
                    value = base_value * 0.6
                elif risk_factor > 0.85:
                    status = "overstock"
                    label = "Overstock (Bahaya)"
                    value = base_value * 1.5
                else:
                    status = "safe"
                    label = "Aman"
                    value = base_value
            else:  # live mode
                if base_value < 200:
                    status = "warning"
                    label = "Restock Needed"
                else:
                    status = "safe"
                    label = "Stock Healthy"
                value = base_value

            map_analytics[region_code] = MapAnalyticsData(
                status=status,
                value=round(value, 1),
                label=label
            )

        # Add some specific overrides for known regions (like in the original mock)
        if level == "35":  # Special case for East Java province
            map_analytics["3507"] = MapAnalyticsData(status="critical", value=120, label="Lonjakan Permintaan (CatBoost)")
            map_analytics["3573"] = MapAnalyticsData(status="safe", value=500, label="Stok Aman")
            map_analytics["3501"] = MapAnalyticsData(status="overstock", value=950, label="Risk: Dead Stock")

        # Generate regional insights (sample regions with demand data)
        regional_insights = []
        sample_regions = [
            ("Kec. Bantul", 12.3),
            ("Kec. Sleman", 18.7),
            ("Kec. Yogyakarta", 9.1),
            ("Kec. Kulon Progo", 15.2)
        ]

        for region_name, base_demand in sample_regions:
            # Add some variation to make it more realistic
            demand_variation = random.uniform(-0.5, 0.5)
            demand = round(base_demand + demand_variation, 1)

            # Generate confidence score
            confidence = random.randint(80, 98)

            # Determine trend based on demand variation
            if demand_variation > 0.2:
                trend = "up"
            elif demand_variation < -0.2:
                trend = "down"
            else:
                trend = "stable"

            # Determine risk level
            if demand < 10:
                risk = "high"
            elif demand < 15:
                risk = "medium"
            else:
                risk = "low"

            regional_insights.append(RegionalInsight(
                name=region_name,
                demand=f"{demand} tons",
                confidence=confidence,
                trend=trend,
                risk=risk
            ))

        return map_analytics, regional_insights
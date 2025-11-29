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

        # Determine if this is a province level (2 digits) or regency level (4+ digits or name)
        is_province_level = level.isdigit() and len(level) == 2
        is_regency_level = (level.isdigit() and len(level) >= 4) or (not level.isdigit() and level not in ["pulau", "indonesia"])

        # For province level, get regency data
        # For regency level, get district/sub-district data
        if is_province_level:
            # Province level - get regencies within this province
            filename = region_mappings.get(level, f"province_{level}")
            if not filename or not os.path.exists(os.path.join("data", "maps", f"{filename}.geojson")):
                # Fallback: generate mock regency codes for this province
                province_prefix = level
                region_codes = [f"{province_prefix}{str(i).zfill(2)}" for i in range(1, 15)]  # Mock 14 regencies
                region_names = [f"Kabupaten/Kota {i}" for i in range(1, 15)]
            else:
                # Load geojson data to get actual regency codes
                geojson_path = os.path.join("data", "maps", f"{filename}.geojson")
                region_codes = []
                region_names = []

                if os.path.exists(geojson_path):
                    try:
                        with open(geojson_path, 'r', encoding='utf-8') as f:
                            geojson_data = json.load(f)

                        # Extract regency codes and names from geojson features
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
                            region_name = (
                                props.get('name') or
                                props.get('NAMOBJ') or
                                props.get('NAME_2') or
                                props.get('district') or
                                props.get('regency_name')
                            )
                            if region_id:
                                region_codes.append(str(region_id))
                                region_names.append(region_name or f"Region {region_id}")
                    except Exception as e:
                        print(f"Error reading geojson {geojson_path}: {e}")
                        # Fallback to mock data
                        province_prefix = level
                        region_codes = [f"{province_prefix}{str(i).zfill(2)}" for i in range(1, 15)]
                        region_names = [f"Kabupaten/Kota {i}" for i in range(1, 15)]
        elif is_regency_level:
          
            filename = region_mappings.get(level, f"id{level}_malang.geojson")
            if not filename:
                filename = f"id{level}_malang.geojson"

            geojson_path = os.path.join("data", "maps", f"{filename}.geojson")
            region_codes = []
            region_names = []

            if os.path.exists(geojson_path):
                try:
                    with open(geojson_path, 'r', encoding='utf-8') as f:
                        geojson_data = json.load(f)

                    # Extract unique district names from geojson features
                    district_names = set()
                    for feature in geojson_data.get('features', []):
                        props = feature.get('properties', {})
                        district_name = props.get('district')
                        if district_name:
                            district_names.add(district_name)

                    # Convert to sorted list and create region codes
                    region_names = sorted(list(district_names))
                    region_codes = [f"{level}_kec_{i}" for i in range(1, len(region_names) + 1)]
                except Exception as e:
                    print(f"Error reading geojson {geojson_path}: {e}")
                    # Fallback to mock data
                    region_codes = [f"{level}_kec_{i}" for i in range(1, 21)]
                    region_names = [f"Kecamatan {i}" for i in range(1, 21)]
            else:
                # Fallback if geojson doesn't exist
                region_codes = [f"{level}_kec_{i}" for i in range(1, 21)]
                region_names = [f"Kecamatan {i}" for i in range(1, 21)]
        else:
            # National level - provinces
            filename = "indonesia"  # Always use indonesia.geojson for national level
            geojson_path = os.path.join("data", "maps", f"{filename}.geojson")
            region_codes = []
            region_names = []

            if os.path.exists(geojson_path):
                try:
                    with open(geojson_path, 'r', encoding='utf-8') as f:
                        geojson_data = json.load(f)

                    # Extract province codes and names from geojson features
                    for feature in geojson_data.get('features', []):
                        props = feature.get('properties', {})
                        region_id = (
                            props.get('prov_id') or
                            props.get('ID') or
                            props.get('id') or
                            props.get('KODE') or
                            props.get('kode') or
                            props.get('bps_code')
                        )
                        region_name = (
                            props.get('prov_name') or
                            props.get('NAME_1') or
                            props.get('provinsi') or
                            props.get('name')
                        )
                        if region_id:
                            region_codes.append(str(region_id))
                            region_names.append(region_name or f"Provinsi {region_id}")
                except Exception as e:
                    print(f"Error reading geojson {geojson_path}: {e}")

            # If no regions found in geojson, use fallback province codes
            if not region_codes:
                region_codes = ["11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "31", "32", "33", "34", "35", "36", "51", "52", "53", "61", "62", "63", "64", "65", "71", "72", "73", "74", "75", "76", "81", "82", "91", "94"]
                region_names = ["ACEH", "SUMATERA UTARA", "SUMATERA BARAT", "RIAU", "JAMBI", "SUMATERA SELATAN", "BENGKULU", "LAMPUNG", "KEPULAUAN BANGKA BELITUNG", "KEPULAUAN RIAU", "DKI JAKARTA", "JAWA BARAT", "JAWA TENGAH", "DAERAH ISTIMEWA YOGYAKARTA", "JAWA TIMUR", "BANTEN", "BALI", "NUSA TENGGARA BARAT", "NUSA TENGGARA TIMUR", "KALIMANTAN BARAT", "KALIMANTAN TENGAH", "KALIMANTAN SELATAN", "KALIMANTAN TIMUR", "KALIMANTAN UTARA", "SULAWESI UTARA", "SULAWESI TENGAH", "SULAWESI SELATAN", "SULAWESI TENGGARA", "GORONTALO", "SULAWESI BARAT", "MALUKU", "MALUKU UTARA", "PAPUA BARAT", "PAPUA SELATAN"]

        # Generate map analytics data
        map_analytics = {}
        region_data = []

        for i, region_code in enumerate(region_codes):
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

            region_name = region_names[i] if i < len(region_names) else f"Region {region_code}"

            map_analytics[region_code] = MapAnalyticsData(
                status=status,
                value=round(value, 1),
                label=label
            )

            # Store region data for sorting
            region_data.append({
                'code': region_code,
                'name': region_name,
                'value': round(value, 1),
                'status': status,
                'label': label
            })

        # Add some specific overrides for known regions (like in the original mock)
        if level == "35":  # Special case for East Java province
            map_analytics["3507"] = MapAnalyticsData(status="critical", value=120, label="Lonjakan Permintaan (CatBoost)")
            map_analytics["3573"] = MapAnalyticsData(status="safe", value=500, label="Stok Aman")
            map_analytics["3501"] = MapAnalyticsData(status="overstock", value=950, label="Risk: Dead Stock")

            # Update region_data as well
            for data in region_data:
                if data['code'] == "3507":
                    data.update({'value': 120, 'status': 'critical', 'label': 'Lonjakan Permintaan (CatBoost)'})
                elif data['code'] == "3573":
                    data.update({'value': 500, 'status': 'safe', 'label': 'Stok Aman'})
                elif data['code'] == "3501":
                    data.update({'value': 950, 'status': 'overstock', 'label': 'Risk: Dead Stock'})

        # Sort regions by importance (critical first, then by value descending) and take top 4
        def get_importance_score(region):
            status_priority = {'critical': 4, 'warning': 3, 'overstock': 2, 'safe': 1}
            return (status_priority.get(region['status'], 0), region['value'])

        sorted_regions = sorted(region_data, key=get_importance_score, reverse=True)
        top_regions = sorted_regions[:4]

        # Generate regional insights from top 4 regions
        regional_insights = []
        for region in top_regions:
            # Generate confidence score
            confidence = random.randint(80, 98)

            # Determine trend based on status
            if region['status'] == 'critical':
                trend = "up"
            elif region['status'] == 'overstock':
                trend = "down"
            else:
                trend = "stable"

            # Determine risk level
            if region['status'] == 'critical':
                risk = "high"
            elif region['status'] == 'warning':
                risk = "medium"
            else:
                risk = "low"

            regional_insights.append(RegionalInsight(
                name=region['name'],
                demand=f"{region['value']} tons",
                confidence=confidence,
                trend=trend,
                risk=risk
            ))

        return map_analytics, regional_insights
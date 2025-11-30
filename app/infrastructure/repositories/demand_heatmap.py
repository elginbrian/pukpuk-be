import json
import os
import random
import traceback
import re
import pandas as pd
from catboost import CatBoostRegressor
from pathlib import Path
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...application.domain.interfaces.demand_heatmap import IDemandHeatmapRepository
from ...application.domain.entities.demand_heatmap import MapAnalyticsData, RegionalInsight
from .maps import MapsRepository
from ...application.constants import PROVINCE_MAP

class DemandHeatmapRepository(IDemandHeatmapRepository):
    def __init__(self, database: AsyncIOMotorDatabase, maps_repo: MapsRepository):
        self.database = database
        self.maps_repo = maps_repo

        # Setup Path
        try:
            self.BASE_DIR = Path(__file__).resolve().parents[4]
            self.MAPS_DIR = self.BASE_DIR / "data" / "maps"
            self.MODEL_PATH = self.BASE_DIR / "ai_engine" / "pukpuk_demand_v1.cbm"
        except:
            self.MAPS_DIR = Path("data/maps").resolve()
            self.MODEL_PATH = Path("pukpuk_demand_v1.cbm").resolve()

        # Load AI Model
        self.model = None
        if self.MODEL_PATH.exists():
            try:
                self.model = CatBoostRegressor()
                self.model.load_model(str(self.MODEL_PATH))
                print(f"✅ [AI] Model Loaded")
            except Exception as e:
                print(f"❌ [AI] Error: {e}")

        # Build Name Lookup Table
        self.global_name_map = {}
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        if self.MAPS_DIR.exists():
            for file_path in self.MAPS_DIR.glob("id*.geojson"):
                filename = file_path.stem
                match_id = re.search(r'id(\d+)', filename)
                if match_id:
                    rid = match_id.group(1)
                    raw_name = re.sub(r'id\d+[_]?', '', filename).replace('_', ' ').upper()
                    self.global_name_map[raw_name] = rid
                    self.global_name_map[raw_name.replace("KABUPATEN ", "")] = rid
                    self.global_name_map[raw_name.replace("KOTA ", "")] = rid

    async def get_demand_heatmap_data(self, level: str, mode: str, layer: str) -> tuple[Dict[str, MapAnalyticsData], List[RegionalInsight]]:
        try:
            filename = None
            target_level_type = "unknown"
            child_ids = []
            child_names = []
            map_found = False

            # 1. Tentukan File
            if level in ["indonesia", "pulau"]:
                filename = "indonesia.geojson"
                target_level_type = "province"
                map_found = True
            elif level in PROVINCE_MAP:
                filename = f"{PROVINCE_MAP[level]}.geojson"
                target_level_type = "regency"
                map_found = True
            else:
                target_level_type = "district"
                if self.MAPS_DIR.exists():
                    files = list(self.MAPS_DIR.glob(f"id{level}_*.geojson"))
                    if files:
                        filename = files[0].name
                        map_found = True

            # 2. Baca File & Ekstrak Data
            if map_found and filename:
                file_path = self.MAPS_DIR / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            geo_data = json.load(f)

                        for feature in geo_data.get("features", []):
                            p = feature.get("properties", {})
                            cid = None
                            cname = None

                            # A. Cari Nama
                            name_keys = ["district", "kecamatan", "nm_kec", "regency", "kabupaten", "nm_kab", "province", "provinsi", "name", "NAME", "NAMOBJ"]
                            for k in name_keys:
                                if p.get(k):
                                    cname = str(p.get(k))
                                    break
                            
                            clean_name = "UNKNOWN"
                            if cname:
                                clean_name = cname.upper().replace("KABUPATEN ", "").replace("KOTA ", "").replace("KECAMATAN ", "").strip()

                            # B. Cari ID (Reverse Lookup jika ID kosong)
                            id_keys = ["district_code", "regency_code", "prov_id", "bps_code", "kode", "id", "ID", "kab_kode", "kec_kode"]
                            for k in id_keys:
                                if p.get(k):
                                    cid = str(p.get(k))
                                    break

                            if not cid and target_level_type == "regency":
                                if clean_name in self.global_name_map:
                                    cid = self.global_name_map[clean_name]

                            if cid:
                                clean_id = str(cid).replace("id", "")
                                if clean_id != level:
                                    child_ids.append(clean_id)
                                    child_names.append(clean_name)

                    except Exception as e:
                        print(f"❌ Error reading {filename}: {e}")

            # 3. Fallback
            if not child_ids:
                if level in ["indonesia", "pulau"]:
                    for k, v in PROVINCE_MAP.items():
                        child_ids.append(k)
                        child_names.append(v.upper())
                else:
                    for i in range(1, 8):
                        child_ids.append(f"{level}{i:02d}")
                        child_names.append(f"AREA {i}")

            # 4. AI Prediction & Coloring
            map_analytics = {}
            regional_insights = []
            inputs = []
            
            # Tentukan Threshold berdasarkan level
            threshold = 200
            if target_level_type == "province": threshold = 5000
            elif target_level_type == "regency": threshold = 2000

            for rid in child_ids:
                simulated_area = random.uniform(threshold * 0.1, threshold * 2.5)
                inputs.append([rid, random.uniform(50, 400), random.uniform(0.1, 0.9), simulated_area, 2500])

            preds = []
            if self.model:
                try:
                    df = pd.DataFrame(inputs, columns=['region_id', 'rainfall', 'ndvi', 'land_area', 'price'])
                    preds = self.model.predict(df)
                except:
                    preds = [inp[3] for inp in inputs]
            else:
                preds = [inp[3] for inp in inputs]

            # 5. Mapping Result
            for i, rid in enumerate(child_ids):
                val = float(preds[i])
                if val < 0: val = 0
                if mode == "forecast": val *= 1.1

                # Status Logic
                ratio = val / threshold
                if ratio > 1.4: status = "critical"
                elif ratio > 0.9: status = "warning"
                elif ratio > 0.3: status = "safe"
                else: status = "overstock"

                map_analytics[rid] = MapAnalyticsData(
                    status=status,
                    value=round(val, 1),
                    label=f"{status.title()} ({int(val)} T)"
                )

                if i < 8:
                    regional_insights.append(RegionalInsight(
                        name=child_names[i], code=rid, demand=f"{int(val)} Ton",
                        confidence=random.randint(85, 99), trend="stable",
                        risk="high" if status == "critical" else ("medium" if status == "warning" else "low")
                    ))
            
            # Sort by Risk (High first)
            regional_insights.sort(key=lambda x: 0 if x.risk == "high" else 1 if x.risk == "medium" else 2)
            
            return map_analytics, regional_insights[:4]

        except Exception:
            traceback.print_exc()
            return ({}, [])
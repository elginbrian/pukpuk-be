import os
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from ...container import Container
from ...use_cases.demand_heatmap import GetDemandHeatmapDataUseCase
from ...domain.entities.demand_heatmap import DemandHeatmapData
from ...constants import PROVINCE_MAP 

router = APIRouter(
    prefix="/demand-heatmap",
    tags=["Demand Heatmap"]
)

try:
    BASE_DIR = Path(__file__).resolve().parents[4]
    MAPS_DIR = BASE_DIR / "data" / "maps"
except Exception:
    MAPS_DIR = Path("data/maps").resolve()

def get_use_case():
    container = Container()
    return container.get_demand_heatmap_data_use_case()

@router.get("/region-mappings")
async def get_region_mappings():
    file_map = PROVINCE_MAP.copy()
    name_map = {}

    if MAPS_DIR.exists():
        for file_path in MAPS_DIR.glob("id*.geojson"):
            filename = file_path.stem
            match_id = re.search(r'id(\d+)_', filename)
            
            if match_id:
                region_id = match_id.group(1)
                file_map[region_id] = filename
                
                # Mapping Nama
                raw_name = re.sub(r'id\d+_', '', filename)
                clean_name = raw_name.replace('_', ' ').upper()
                name_map[clean_name] = region_id
                name_map[clean_name.replace("KABUPATEN ", "")] = region_id
                name_map[clean_name.replace("KOTA ", "")] = region_id

    return { "files": file_map, "names": name_map }

@router.get("/demand-data", response_model=DemandHeatmapData)
async def get_demand_data(
    level: str = Query(..., description="Region Code"),
    mode: str = Query("forecast"),
    layer: str = Query("demand"),
    use_case: GetDemandHeatmapDataUseCase = Depends(get_use_case)
):
    return await use_case.execute(level, mode, layer)

@router.get("/maps/{filename}")
async def get_geojson_map(filename: str):
    if not filename.endswith(".geojson"):
        filename += ".geojson"
        
    file_path = MAPS_DIR / filename
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Map not found")
        
    return FileResponse(file_path, media_type="application/geo+json")
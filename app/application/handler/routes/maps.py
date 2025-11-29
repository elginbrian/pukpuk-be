from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from ...use_cases.maps import MapsUseCase
from ...infrastructure.repositories.maps import MapsRepository
from ...infrastructure.database.database import get_database
import os

router = APIRouter()

@router.get("/maps/{filename}")
async def get_geojson(filename: str):
    if not filename.endswith('.geojson'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = os.path.join("data", "maps", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type='application/json')

@router.get("/region-mappings")
async def get_region_mappings(
    maps_use_case: MapsUseCase = Depends(lambda: MapsUseCase(MapsRepository(get_database())))
):
    """Get region to geojson filename mappings."""
    return await maps_use_case.get_region_mappings()
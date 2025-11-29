from beanie import Document
from pydantic import BaseModel
from typing import Dict

class RegionMapping(Document):
    region_code: str
    geojson_filename: str

    class Settings:
        name = "region_mappings"

class RegionMappings(Document):
    mappings: Dict[str, str]

    class Settings:
        name = "region_mappings_config"
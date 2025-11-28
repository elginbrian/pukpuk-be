from beanie import Document
from pydantic import BaseModel
from typing import List

# Route Optimization Entities
class RouteOption(BaseModel):
    id: str  # "fastest", "cheapest", "greenest"
    distance: float  # in km
    duration: str  # e.g., "3h 45min"
    fuel_cost: float  # in IDR
    toll_cost: float  # in IDR
    co2: float  # in kg
    path: str  # route description
    waypoints: List[List[float]]  # list of [lat, lng] coordinates

class RouteOptimizationRequest(BaseModel):
    origin: str
    destination: str
    vehicle_type: str
    load_capacity: float

class RouteOptimizationResponse(BaseModel):
    fastest: RouteOption
    cheapest: RouteOption
    greenest: RouteOption

# Route Data Entities for Database
class Location(Document):
    code: str  # e.g., "plant-a", "warehouse-b"
    name: str  # e.g., "Plant A - Karawang"
    coordinates: List[float]  # [latitude, longitude]
    type: str  # "plant", "warehouse", "kiosk"
    address: str
    icon_url: str  # URL to the marker icon

    class Settings:
        name = "locations"

class RouteConfiguration(Document):
    origin: str  # location code
    destination: str  # location code
    vehicle_type: str
    load_capacity: float
    fastest_distance: float
    cheapest_distance: float
    greenest_distance: float
    fastest_path: List[str]  # list of location codes
    cheapest_path: List[str]
    greenest_path: List[str]

    class Settings:
        name = "route_configurations"

class Vehicle(Document):
    code: str  # e.g., "truck-small"
    name: str  # e.g., "Small Truck (3-5 tons)"
    min_capacity: float  # minimum load capacity in tons
    max_capacity: float  # maximum load capacity in tons
    fuel_consumption: float  # km/L
    average_speed: float  # km/h
    co2_factor: float  # kg/km
    type: str  # "truck"

    class Settings:
        name = "vehicles"
from abc import ABC, abstractmethod
from typing import List
from ..entities.route_optimization import RouteOptimizationResponse, RouteOptimizationRequest, Location, Vehicle, RouteConfiguration

class IRouteOptimizationRepository(ABC):
    @abstractmethod
    async def optimize_route(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        pass

    @abstractmethod
    async def get_locations(self) -> List[Location]:
        pass

    @abstractmethod
    async def get_vehicles(self) -> List[Vehicle]:
        pass

    @abstractmethod
    async def get_route_configurations(self) -> List[RouteConfiguration]:
        pass
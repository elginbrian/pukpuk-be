from abc import ABC, abstractmethod
from typing import List
from ..entities.route_optimization import RouteOptimizationResponse, RouteOptimizationRequest, Location, RouteConfiguration, Vehicle

class IOptimizeRouteUseCase(ABC):
    @abstractmethod
    async def execute(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        pass

class IGetLocationsUseCase(ABC):
    @abstractmethod
    async def execute(self) -> List[Location]:
        pass

class IGetVehiclesUseCase(ABC):
    @abstractmethod
    async def execute(self) -> List[Vehicle]:
        pass

class IGetRouteConfigurationsUseCase(ABC):
    @abstractmethod
    async def execute(self) -> List[RouteConfiguration]:
        pass
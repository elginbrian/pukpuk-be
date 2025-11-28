from typing import List
from ..domain.entities.route_optimization import RouteOptimizationRequest, RouteOptimizationResponse, Location, Vehicle, RouteConfiguration
from ..domain.use_cases.route_optimization import IOptimizeRouteUseCase, IGetLocationsUseCase, IGetVehiclesUseCase, IGetRouteConfigurationsUseCase
from ..domain.interfaces.route_optimization import IRouteOptimizationRepository

class OptimizeRouteUseCase(IOptimizeRouteUseCase):
    def __init__(self, route_repo: IRouteOptimizationRepository):
        self.route_repo = route_repo

    async def execute(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        return await self.route_repo.optimize_route(request)


class GetLocationsUseCase(IGetLocationsUseCase):
    def __init__(self, route_repo: IRouteOptimizationRepository):
        self.route_repo = route_repo

    async def execute(self) -> List[Location]:
        return await self.route_repo.get_locations()


class GetVehiclesUseCase(IGetVehiclesUseCase):
    def __init__(self, route_repo: IRouteOptimizationRepository):
        self.route_repo = route_repo

    async def execute(self) -> List[Vehicle]:
        return await self.route_repo.get_vehicles()


class GetRouteConfigurationsUseCase(IGetRouteConfigurationsUseCase):
    def __init__(self, route_repo: IRouteOptimizationRepository):
        self.route_repo = route_repo

    async def execute(self) -> List[RouteConfiguration]:
        return await self.route_repo.get_route_configurations()
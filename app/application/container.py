"""Dependency Injection Container"""

from dependency_injector import containers, providers
from ..infrastructure.config.settings import Settings
from ..infrastructure.database.database import get_database
from ..infrastructure.repositories import ForecastRepository, MetricsRepository
from ..application.use_cases import GetForecastUseCase, GetMetricsUseCase, SimulateScenarioUseCase


class Container(containers.DeclarativeContainer):
    """Application dependency injection container"""

    # Configuration
    config = providers.Singleton(Settings)

    # Database
    database = providers.Singleton(get_database)

    # Repositories
    forecast_repository = providers.Singleton(ForecastRepository, database=database)
    metrics_repository = providers.Singleton(MetricsRepository, database=database)

    # Use Cases
    get_forecast_use_case = providers.Singleton(GetForecastUseCase, forecast_repo=forecast_repository, metrics_repo=metrics_repository)
    get_metrics_use_case = providers.Singleton(GetMetricsUseCase, metrics_repo=metrics_repository)
    simulate_scenario_use_case = providers.Singleton(SimulateScenarioUseCase, forecast_repo=forecast_repository)


# Global container instance
container = Container()
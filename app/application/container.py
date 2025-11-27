"""Dependency Injection Container"""

from dependency_injector import containers, providers
from ..infrastructure.config.settings import Settings
from ..infrastructure.database.database import get_database_sync
from ..infrastructure.repositories import ForecastRepository, MetricsRepository
from ..application.use_cases import GetForecastUseCase, GetMetricsUseCase, SimulateScenarioUseCase


class Container(containers.DeclarativeContainer):
    """Application dependency injection container"""

    # Configuration
    config = providers.Singleton(Settings)

    @providers.Singleton
    def database_factory():
        try:
            return get_database_sync()
        except RuntimeError:
            # Return None if database not available - repositories will handle this
            return None

    # Repositories
    forecast_repository = providers.Singleton(ForecastRepository, database=database_factory)
    metrics_repository = providers.Singleton(MetricsRepository, database=database_factory)

    # Use Cases
    get_forecast_use_case = providers.Singleton(GetForecastUseCase, forecast_repo=forecast_repository, metrics_repo=metrics_repository)
    get_metrics_use_case = providers.Singleton(GetMetricsUseCase, metrics_repo=metrics_repository)
    simulate_scenario_use_case = providers.Singleton(SimulateScenarioUseCase, forecast_repo=forecast_repository)


# Global container instance
container = Container()
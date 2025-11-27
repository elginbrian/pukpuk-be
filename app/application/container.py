"""Dependency Injection Container"""

from dependency_injector import containers, providers
from ..infrastructure.config.settings import Settings
from ..infrastructure.database.database import get_database_sync
from ..infrastructure.repositories import ForecastRepository, MetricsRepository, AIInsightsRepository, ChatSessionRepository
from ..application.use_cases import GetForecastUseCase, GetMetricsUseCase, SimulateScenarioUseCase, GenerateAIInsightUseCase, ChatSessionUseCase


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
    ai_insights_repository = providers.Singleton(AIInsightsRepository, database=database_factory)
    chat_session_repository = providers.Singleton(ChatSessionRepository, database=database_factory)

    # Use Cases
    get_forecast_use_case = providers.Singleton(GetForecastUseCase, forecast_repo=forecast_repository, metrics_repo=metrics_repository)
    get_metrics_use_case = providers.Singleton(GetMetricsUseCase, metrics_repo=metrics_repository)
    simulate_scenario_use_case = providers.Singleton(SimulateScenarioUseCase, forecast_repo=forecast_repository)
    generate_ai_insight_use_case = providers.Singleton(GenerateAIInsightUseCase, ai_insights_repo=ai_insights_repository, forecast_repo=forecast_repository, metrics_repo=metrics_repository, chat_session_repo=chat_session_repository)
    chat_session_use_case = providers.Singleton(ChatSessionUseCase, chat_session_repo=chat_session_repository)


# Global container instance
container = Container()
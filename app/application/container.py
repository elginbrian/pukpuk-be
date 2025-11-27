"""Dependency Injection Container"""

from dependency_injector import containers, providers
from ..infrastructure.config.settings import Settings


class Container(containers.DeclarativeContainer):
    """Application dependency injection container"""

    # Configuration
    config = providers.Singleton(Settings)

    # Infrastructure providers will be added here
    # database = providers.Singleton(DatabaseConnection, config=config)
    # repositories will be added here
    # use_cases will be added here
    # services will be added here


# Global container instance
container = Container()
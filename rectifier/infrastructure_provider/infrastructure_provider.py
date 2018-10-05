from abc import ABC, abstractmethod


class InfrastructureProviderError(RuntimeError):
    """Raises when an errors occurs in
    a service implementation."""

    pass


class InfrastructureProvider(ABC):
    """The provider of the infrastructure (consumers). Able to scale the consumers."""

    @abstractmethod
    def scale(self, app_name: str, queue_name: str, consumers_count: int) -> None:
        """Scale the infrastructure for the given queue_name to the given consumers_count"""

    @abstractmethod
    def broker_uri(self, app_name: str) -> str:
        """Gets the broker uri for a given app name"""

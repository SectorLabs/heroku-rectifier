from abc import ABC, abstractmethod
from typing import Dict


class InfrastructureProviderError(RuntimeError):
    """Raises when an errors occurs in
    a service implementation."""

    pass


class InfrastructureProvider(ABC):
    """The provider of the infrastructure (consumers). Able to scale the consumers."""

    @abstractmethod
    def scale(self, app_name: str, scale_requests: Dict[str, int]) -> None:
        """Scale the infrastructure in batch for the given queue_names to the given consumers_counts"""

    @abstractmethod
    def broker_uri(self, app_name: str) -> str:
        """Gets the broker uri for a given app name"""

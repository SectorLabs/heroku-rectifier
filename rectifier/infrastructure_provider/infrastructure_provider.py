from abc import ABC, abstractmethod


class InfrastructureProviderError(RuntimeError):
    """Raises when an errors occurs in
    a service implementation."""

    pass


class InfrastructureProvider(ABC):
    @abstractmethod
    def scale(self, queue_name: str, consumers_count: int) -> None:
        """Scale the infrastructure for the given queue_name to the given consumers_count"""

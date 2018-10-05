from abc import ABC, abstractmethod


class InfrastructureProvider(ABC):

    @abstractmethod
    def scale(self, queue_name: str, consumers_count: int) -> None:
        pass


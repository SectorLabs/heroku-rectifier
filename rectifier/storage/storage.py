from abc import ABC, abstractmethod
from typing import Optional, Any


class StorageSubscription(ABC):
    @abstractmethod
    def get_message(self):
        pass


class Storage(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def publish(self, channel: str, message: Optional[Any] = None):
        pass

    @abstractmethod
    def subscribe(self, channel: str) -> StorageSubscription:
        pass


from abc import ABC, abstractmethod
from typing import Optional, Any


class StorageSubscription(ABC):
    @abstractmethod
    def get_message(self):
        """Returns the next message available for this subscription (if one exists)."""


class Storage(ABC):
    """
    An abstraction of a key-value persistent storage.
    """

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get the value of the given key."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set the value of a given key."""

    @abstractmethod
    def publish(self, channel: str, message: Optional[Any] = None):
        """Publish a message to a channel."""

    @abstractmethod
    def subscribe(self, channel: str) -> StorageSubscription:
        """Subscribe to a channel."""

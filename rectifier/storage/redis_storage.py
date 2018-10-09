from typing import Optional, Any

import redis
from redis.client import PubSub

from rectifier.storage.storage import Storage, StorageSubscription
from rectifier import settings


class RedisSubscription(StorageSubscription):
    def __init__(self, pubsub: PubSub) -> None:
        self.pubsub = pubsub

    def get_message(self):
        return self.pubsub.get_message()


class RedisStorage(Storage):
    def __init__(self) -> None:
        self.redis = redis.StrictRedis.from_url(settings.REDIS_URL)

    def set(self, key: str, value: Any) -> None:
        return self.redis.set(key, value)

    def get(self, key: str) -> Any:
        return self.redis.get(key)

    def subscribe(self, channel: str) -> StorageSubscription:
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return RedisSubscription(pubsub)

    def publish(self, channel: str, message: Optional[Any] = None):
        return self.redis.publish(channel, message)

from typing import Optional, Any

from rectifier.storage import Storage, StorageSubscription


class RedisStorageMockSubscription(StorageSubscription):
    def get_message(self):
        return 'message'


class RedisStorageMock(Storage):
    def __init__(self):
        self.data = dict(
            config=b'{"queues":{"rectifier":{"intervals":[0,10,20,30],"workers":[1,5,50,51],"cooldown":30}}}'
        )

    def get(self, key: str) -> Any:
        return self.data.get(key)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def publish(self, channel: str, message: Optional[Any] = None):
        pass

    def subscribe(self, channel: str) -> StorageSubscription:
        return RedisStorageMockSubscription()

from typing import Any, Optional

from rectifier.storage import Storage, StorageSubscription


class RedisStorageMockSubscription(StorageSubscription):
    def get_message(self):
        return 'message'


class RedisStorageMock(Storage):
    def __init__(self):
        self.data = dict(
            config=b'{"rectifier":{"q1":{"intervals":[0,10,20,30],"workers":[1,5,50,51],"cooldown":30,"consumers_formation_name":"worker_rectifier"}},'
            b'"rectifier2":{"q21":{"intervals":[0,10,22,85],"workers":[1,5,6,7],"cooldown":120,"consumers_formation_name":"worker_rectifier2"}}}'
        )

    def get(self, key: str) -> Any:
        return self.data.get(key)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def publish(self, channel: str, message: Optional[Any] = None):
        pass

    def subscribe(self, channel: str) -> StorageSubscription:
        return RedisStorageMockSubscription()

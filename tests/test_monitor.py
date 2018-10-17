import pickle
from collections import defaultdict

from freezegun import freeze_time

from rectifier import settings
from rectifier.infrastructure_provider import InfrastructureProvider
from rectifier.message_brokers import RabbitMQ
from rectifier.rectifier import Rectifier
from tests.redis_mock import RedisStorageMock

from .env import env  # noqa


class InfrastructureProviderMock(InfrastructureProvider):
    def __init__(self):
        self.consumers = defaultdict(int)
        self.called_count = 0

    def scale(self, queue_name: str, consumers_count: int) -> None:
        self.consumers[queue_name] = consumers_count
        self.called_count += 1


def test_monitor(env):
    storage = RedisStorageMock()
    infrastructure_provider = InfrastructureProviderMock()

    storage.set(
        settings.REDIS_CONFIG_KEY,
        b'{"queues":{"q1":{"intervals":[0,10,100],"workers":[1,2,3],"cooldown":60,"consumers_formation_name":"worker_q1"}}}',
    )
    rectifier = Rectifier(
        broker=RabbitMQ(),
        storage=storage,
        infrastructure_provider=infrastructure_provider,
    )

    with freeze_time("2012-01-14 03:00:00") as frozen_time:
        # Should scale to one consumer, because the workers count
        # for the 0 - 10 interval is 1
        env.default_vhost.set_queue('q1')
        rectifier.run()

        assert infrastructure_provider.called_count == 1
        assert infrastructure_provider.consumers['worker_q1'] == 1

        # Set the queue to one consumer and 10 messages
        env.default_vhost.set_queue('q1', 1, 10)

        # Move 59 seconds in the future.
        # As the cooldown is not yet elapsed, nothing should happen.
        frozen_time.move_to('2012-01-14 03:00:59')
        rectifier.run()
        assert infrastructure_provider.called_count == 1
        assert infrastructure_provider.consumers['worker_q1'] == 1

        # Move one more second. The CD is elapsed. Check the scaling happened.
        frozen_time.move_to('2012-01-14 03:01:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['worker_q1'] == 2

        # Set the queue to more than 100 messages, but set the workers to 3 (to simulate a manual change)
        env.default_vhost.set_queue('q1', 3, 123)

        # Move ahead to more the 60 seconds in the future. As the workers were manually adjusted,
        # check that they're not scaled anymore
        frozen_time.move_to('2012-01-14 03:02:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['worker_q1'] == 2

        # Consume messages from the queue
        env.default_vhost.set_queue('q1', 3, 75)

        # Check that downscaling works
        rectifier.run()
        assert infrastructure_provider.called_count == 3
        assert infrastructure_provider.consumers['worker_q1'] == 2

        # Check that the CD is respected for downscaling too
        env.default_vhost.set_queue('q1', 2, 7)
        frozen_time.move_to('2012-01-14 03:02:01')
        assert infrastructure_provider.called_count == 3
        assert infrastructure_provider.consumers['worker_q1'] == 2

        env.default_vhost.set_queue('q1', 2, 0)
        frozen_time.move_to('2012-01-14 03:03:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 4
        assert infrastructure_provider.consumers['worker_q1'] == 1


def monitor_with_no_config(env):
    storage = RedisStorageMock()
    infrastructure_provider = InfrastructureProviderMock()

    storage.set(settings.REDIS_CONFIG_KEY, None)
    rectifier = Rectifier(
        broker=RabbitMQ(),
        storage=storage,
        infrastructure_provider=infrastructure_provider,
    )

    assert not storage.get(settings.REDIS_CONFIG_KEY)
    assert not pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES))
    rectifier.run()

    assert infrastructure_provider.called_count == 0
    assert not storage.get(settings.REDIS_CONFIG_KEY)
    assert not pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES))

    storage.set(
        settings.REDIS_CONFIG_KEY,
        b'{"queues":{"q1":{"intervals":[0,10,100],"workers":[1,2,3],"cooldown":60,"consumers_formation_name":"worker_q1"}}}',
    )

    with freeze_time("2012-01-14 03:00:00") as frozen_time:
        # Should scale to one consumer, because the workers count
        # for the 0 - 10 interval is 1
        env.default_vhost.set_queue('q1')
        rectifier.run()

        assert infrastructure_provider.called_count == 1
        assert infrastructure_provider.consumers['worker_q1'] == 1

        assert pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES)) == dict(
            q1=frozen_time
        )

        frozen_time.move_to('2012-01-14 03:01:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['worker_q1'] == 2
        assert pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES)) == dict(
            q1=frozen_time
        )

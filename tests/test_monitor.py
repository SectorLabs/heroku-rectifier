import pickle
from collections import defaultdict
from typing import Dict

from freezegun import freeze_time

from rectifier import settings
from rectifier.infrastructure_provider import InfrastructureProvider
from rectifier.message_brokers import RabbitMQ
from rectifier.rectifier import Rectifier
from tests.redis_mock import RedisStorageMock

from .env import env  # noqa


class InfrastructureProviderMock(InfrastructureProvider):
    def __init__(self, env):
        self.consumers = defaultdict(lambda: defaultdict(int))
        self.called_count = 0
        self.env = env

    def scale(self, app_name: str, updates: Dict[str, int]) -> None:
        for queue_name, consumers_count in updates.items():
            self.consumers[app_name][queue_name] = consumers_count

        self.called_count += 1

    def broker_uri(self, app_name: str):
        return self.env.rabbit_mq_uri(app_name)


def test_monitor(env):
    storage = RedisStorageMock()
    infrastructure_provider = InfrastructureProviderMock(env)

    storage.set(
        settings.REDIS_CONFIG_KEY,
        b'{"rectifier":{"q1":{"intervals":[0,10,100],"workers":[1,2,3],"cooldown":60,"consumers_formation_name":"worker_q1"}},'
        b'"rectifier2":{"q2":{"intervals":[0,10,100],"workers":[2,4,6],"cooldown":30,"consumers_formation_name":"worker_q2"}}}',
    )
    rectifier = Rectifier(
        broker=RabbitMQ(),
        storage=storage,
        infrastructure_provider=infrastructure_provider,
    )

    with freeze_time("2012-01-14 03:00:00") as frozen_time:
        env.rabbitmq.set_queue('rectifier', 'q1')
        env.rabbitmq.set_queue('rectifier2', 'q2')
        rectifier.run()

        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 1
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 2

        # Update the queues. Increase the messages
        env.rabbitmq.set_queue('rectifier', 'q1', 1, 10)
        env.rabbitmq.set_queue('rectifier2', 'q2', 1, 12)

        # Move 29 seconds in the future.
        # As the cooldown is not yet elapsed for either queue, nothing should happen.
        frozen_time.move_to('2012-01-14 03:00:29')
        rectifier.run()
        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 1
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 2

        # Move one more second. The CD is elapsed for q2. Check the scaling happened.
        frozen_time.move_to('2012-01-14 03:00:30')
        rectifier.run()
        assert infrastructure_provider.called_count == 3
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 1
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 4

        # Update the queues. Increase the messages
        env.rabbitmq.set_queue('rectifier2', 'q2', 4, 12)

        # Check that the other queue gets updated..
        frozen_time.move_to('2012-01-14 03:01:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 4
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 2
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 4

        # Set q1 to more than 100 messages, but set the workers to 3 (to simulate a manual change)
        env.rabbitmq.set_queue('rectifier', 'q1', 3, 123)

        # Move ahead to more the 60 seconds in the future. As the workers were manually adjusted,
        # check that they're not scaled again.
        frozen_time.move_to('2012-01-14 03:02:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 4
        # This is still two because scale() wasn't actually called since the balancer
        # noticed that the workers don't have to be balanced.
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 2
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 4

        # Consume messages from the queue
        env.rabbitmq.set_queue('rectifier', 'q1', 3, 75)

        # Check that downscaling works
        rectifier.run()
        assert infrastructure_provider.called_count == 5
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 2

        # Check that the CD is respected for downscaling too
        env.rabbitmq.set_queue('rectifier', 'q1', 2, 7)
        env.rabbitmq.set_queue('rectifier2', 'q2', 2, 7)
        frozen_time.move_to('2012-01-14 03:02:01')
        assert infrastructure_provider.called_count == 5
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 2
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 4

        env.rabbitmq.set_queue('rectifier', 'q1', 2, 0)
        frozen_time.move_to('2012-01-14 03:03:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 6
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 1
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 4

        env.rabbitmq.set_queue('rectifier', 'q1', 1, 0)
        env.rabbitmq.set_queue('rectifier2', 'q2', 3, 0)
        frozen_time.move_to('2012-01-14 03:04:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 7
        assert infrastructure_provider.consumers['rectifier']['worker_q1'] == 1
        assert infrastructure_provider.consumers['rectifier2']['worker_q2'] == 2


def test_monitor_with_no_config(env):
    storage = RedisStorageMock()
    infrastructure_provider = InfrastructureProviderMock(env)

    storage.set(settings.REDIS_CONFIG_KEY, None)
    rectifier = Rectifier(
        broker=RabbitMQ(),
        storage=storage,
        infrastructure_provider=infrastructure_provider,
    )

    assert not storage.get(settings.REDIS_CONFIG_KEY)
    assert not storage.get(settings.REDIS_UPDATE_TIMES)
    rectifier.run()

    assert infrastructure_provider.called_count == 0
    assert not storage.get(settings.REDIS_CONFIG_KEY)
    assert not storage.get(settings.REDIS_UPDATE_TIMES)


def test_update_time_storage(env):
    storage = RedisStorageMock()
    infrastructure_provider = InfrastructureProviderMock(env)

    rectifier = Rectifier(
        broker=RabbitMQ(),
        storage=storage,
        infrastructure_provider=infrastructure_provider,
    )

    storage.set(
        settings.REDIS_CONFIG_KEY,
        b'{"rectify":{"q1":{"intervals":[0,10,100],"workers":[1,2,3],"cooldown":60,"consumers_formation_name":"worker_q1"}}}',
    )

    with freeze_time("2012-01-14 03:00:00") as frozen_time:
        # Should scale to one consumer, because the workers count
        # for the 0 - 10 interval is 1
        env.rabbitmq.set_queue('rectify', 'q1')
        rectifier.run()

        assert infrastructure_provider.called_count == 1
        assert infrastructure_provider.consumers['rectify']['worker_q1'] == 1

        update_times = pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES))
        assert update_times['rectify']['q1'] == frozen_time.time_to_freeze

        env.rabbitmq.set_queue('rectify', 'q1', 1, 11)
        frozen_time.move_to('2012-01-14 03:01:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['rectify']['worker_q1'] == 2

        update_times = pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES))
        assert update_times['rectify']['q1'] == frozen_time.time_to_freeze

        old_time = frozen_time.time_to_freeze
        env.rabbitmq.set_queue('rectify', 'q1', 1, 2)
        frozen_time.move_to('2012-01-14 03:11:00')
        rectifier.run()
        assert infrastructure_provider.called_count == 2
        assert infrastructure_provider.consumers['rectify']['worker_q1'] == 2
        update_times = pickle.loads(storage.get(settings.REDIS_UPDATE_TIMES))
        assert update_times['rectify']['q1'] == old_time

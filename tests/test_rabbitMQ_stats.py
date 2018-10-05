import pytest

from rectifier.message_brokers import RabbitMQ
from rectifier.queue.queue import Queue

from .env import env  # noqa


@pytest.mark.parametrize('config, queue_names, output', [
    ([('rectifier', 1, 1000)], ['rectifier'],
     [Queue(queue_name='rectifier', consumers_count=1, messages=1000)]),
    ([('rectifier', 1, 10),
      ('rectifier2', 2, 30)], ['rectifier', 'rectifier2'], [
          Queue(queue_name='rectifier', consumers_count=1, messages=10),
          Queue(queue_name='rectifier2', consumers_count=2, messages=30)
      ]),
    ([('rectifier', 1, 10), ('rectifier2', 2, 30)], ['rectifier'],
     [Queue(queue_name='rectifier', consumers_count=1, messages=10)]),
])
def test_get_current_load(config, queue_names, output, env):
    rabbitMQ = RabbitMQ(env.config.rabbitMQ_config)
    for queue in config:
        env.default_vhost.set_queue(*queue)

    queues = rabbitMQ.queues(queue_names, rabbitMQ.stats())
    for queue in output:
        assert queue in queues

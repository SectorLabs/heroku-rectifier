import pytest

from rectifier.message_brokers import RabbitMQ
from rectifier.queue.queue import Queue

from .env import env  # noqa


@pytest.mark.parametrize(
    'config, interest_queues, output',
    [
        (
            [('app', 'rectifier', 1, 1000)],
            ['rectifier'],
            [Queue(queue_name='rectifier', consumers_count=1, messages=1000)],
        ),
        (
            [('app', 'rectifier', 1, 10), ('app', 'rectifier2', 2, 30)],
            ['rectifier', 'rectifier2'],
            [
                Queue(queue_name='rectifier', consumers_count=1, messages=10),
                Queue(queue_name='rectifier2', consumers_count=2, messages=30),
            ],
        ),
        (
            [('app', 'rectifier', 1, 10), ('app', 'rectifier2', 2, 30)],
            ['rectifier'],
            [Queue(queue_name='rectifier', consumers_count=1, messages=10)],
        ),
    ],
)
def test_get_current_load(config, interest_queues, output, env):
    for queue in config:
        env.rabbitmq.set_queue(*queue)

    interest_queues = RabbitMQ.queues(
        interest_queues, RabbitMQ.stats(env.rabbit_mq_uri(app='app'))
    )
    for queue in output:
        assert queue in interest_queues


def test_get_current_load_missing_queue(env):
    """Tests whether trying to stats for a queue
    that doesn't exists doesn't make things crash."""

    interest_queues = RabbitMQ.queues(
        ["byebyequeue"],
        RabbitMQ.stats(env.rabbit_mq_uri(app='myapp')),
    )

    assert len(interest_queues) == 0

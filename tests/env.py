import pytest

from rectifier.config import Config, BalancerConfig, QueueConfig, RabbitMQConfig

from .rabbitmq_mock import RabbitMQAPIMock


class TestableEnv:
    """Wrapper for providing mocked services and default
    test-able configuration."""

    DEFAULT_BALANCER_GROUP = 'mybalancer'
    DEFAULT_BALANCER = 'myworker'
    DEFAULT_QUEUE = 'myqueue'
    DEFAULT_VHOST = 'myvhost'

    def __init__(self):
        self.rabbitmq = RabbitMQAPIMock()

        queues = [
            QueueConfig(
                intervals=[1, 10, 20, 30],
                workers=[1, 5, 50, 500],
                cooldown=600,
                queue_name='queue')
        ]

        balancer_config = BalancerConfig(queues=queues)

        rabbitMQ_config = RabbitMQConfig(
            host=self.rabbitmq.host,
            port=self.rabbitmq.port,
            vhost=self.DEFAULT_VHOST,
            user='',
            password='',
            secure=False)

        self.config = Config(
            rabbitMQ_config=rabbitMQ_config, balancer_config=balancer_config)

    @property
    def default_vhost(self):
        """Gets a reference to the default RabbitMQ virtual host."""

        return self.rabbitmq.vhosts[self.DEFAULT_VHOST]

    def start(self):
        """Starts the test-able environment."""

        self.rabbitmq.start()

    def stop(self):
        """Stops the test-able environment."""

        self.rabbitmq.stop()


@pytest.fixture(scope='function')
def env():
    """Provides a test-able environment to the test,
    this includes mocked configurations and services
    as well as utilities to faciliate testing."""

    env = TestableEnv()
    env.start()
    yield env
    env.stop()

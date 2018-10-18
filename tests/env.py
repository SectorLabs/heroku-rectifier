import pytest

from rectifier import settings
from rectifier.config import Config, CoordinatorConfig, QueueConfig, AppConfig

from .rabbitmq_mock import RabbitMQAPIMock


class TestableEnv:
    """Wrapper for providing mocked services and default
    test-able configuration."""

    def __init__(self):
        self.rabbitmq = RabbitMQAPIMock()

        apps = dict(
            rectifier=AppConfig(
                dict(
                    queue=QueueConfig(
                        intervals=[1, 10, 20, 30],
                        workers=[1, 5, 50, 500],
                        cooldown=600,
                        queue_name='queue',
                        consumers_formation_name='worker_queue',
                    )
                )
            )
        )

        coordinator_config = CoordinatorConfig(apps=apps)
        self.config = Config(coordinator_config=coordinator_config)

    def start(self):
        """Starts the test-able environment."""

        self.rabbitmq.start()

    def stop(self):
        """Stops the test-able environment."""

        self.rabbitmq.stop()

    def rabbit_mq_uri(self, app):
        host = '%s:%s' % (self.rabbitmq.host, self.rabbitmq.port)
        return 'amqp://%s:%s@%s/%s' % ('guest', 'guest', host, app)


@pytest.fixture(scope='function')
def env():
    """Provides a test-able environment to the test,
    this includes mocked configurations and services
    as well as utilities to faciliate testing."""

    env = TestableEnv()
    env.start()
    settings.RABBIT_MQ_SECURE = False
    yield env
    env.stop()

import time

import structlog

from rectifier.balancer import Balancer
from rectifier.config import ConfigReader
from rectifier.infrastructure_provider import Heroku
from rectifier.message_brokers import RabbitMQ
from rectifier.monitors import Monitor
from rectifier.storage.redis_storage import RedisStorage
from rectifier.storage.storage import Storage
from rectifier import settings

LOGGER = structlog.get_logger(__name__)


class Rectifier:
    @classmethod
    def monitor(cls, storage: Storage):
        config_reader = ConfigReader(storage=storage)

        rabbitMQ = RabbitMQ()
        balancer = Balancer(config=config_reader.config.balancer_config)
        heroku = Heroku()

        return Monitor(
            broker=rabbitMQ, infrastructure_provider=heroku, balancer=balancer)

    @classmethod
    def run(cls):
        redis_store = RedisStorage()

        monitor = cls.monitor(redis_store)
        subscription = redis_store.subscribe(settings.REDIS_CONFIG_KEY)

        while True:
            message = subscription.get_message()
            if message:
                LOGGER.info('Updating configuration.')
                monitor = cls.monitor(redis_store)

            monitor.scale()
            time.sleep(1)

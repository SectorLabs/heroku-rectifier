import time
from typing import Optional

import structlog

from rectifier.consumer_updates_coordinator import ConsumerUpdatesCoordinator
from rectifier.config import ConfigReader
from rectifier.infrastructure_provider import (
    InfrastructureProvider,
    InfrastructureProviderError,
)
from rectifier.message_brokers import Broker
from rectifier.message_brokers.rabbitmq import BrokerError
from rectifier.storage import Storage
from rectifier import settings

LOGGER = structlog.get_logger(__name__)


class Rectifier:
    broker: Broker
    balancer: Optional[ConsumerUpdatesCoordinator]
    infrastructure_provider: InfrastructureProvider

    def __init__(
        self,
        storage: Storage,
        broker: Broker,
        infrastructure_provider: InfrastructureProvider,
    ) -> None:
        self.storage = storage
        self.broker = broker
        self.infrastructure_provider = infrastructure_provider

        self.subscription = self.storage.subscribe(settings.REDIS_CONFIG_KEY)

        self.update_configuration()

    def update_configuration(self) -> None:
        config_reader = ConfigReader(storage=self.storage)

        if not config_reader.config:
            self.balancer = None
            return

        self.balancer = ConsumerUpdatesCoordinator(
            config=config_reader.config.coordinator_config, storage=self.storage
        )

    def run(self):
        message = self.subscription.get_message()
        if message:
            LOGGER.info('Updating configuration.')
            self.update_configuration()

        self.scale()

    def scale(self):
        if not self.balancer:
            return

        try:
            queues = self.broker.queues(self.balancer.config.queues.keys())
        except BrokerError:
            return

        for queue in queues:
            new_consumer_count = self.balancer.compute_consumers_count(queue)
            if new_consumer_count is None:
                continue

            try:
                self.infrastructure_provider.scale(queue.queue_name, new_consumer_count)
            except InfrastructureProviderError:
                pass

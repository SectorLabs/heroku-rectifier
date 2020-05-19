from typing import Optional

import structlog

from rectifier import settings
from rectifier.config import ConfigParser, AppMode
from rectifier.consumer_updates_coordinator import ConsumerUpdatesCoordinator
from rectifier.infrastructure_provider import (
    InfrastructureProvider,
    InfrastructureProviderError,
)
from rectifier.message_brokers import Broker
from rectifier.message_brokers.rabbitmq import BrokerError
from rectifier.storage import Storage

LOGGER = structlog.get_logger(__name__)


class Rectifier:
    """
    The main _controller_ of the autoscaler.

    Keeps track over the configuration, updates everything accordingly.
    Checks the queue stats, asks for coordination on whether the consumers should be scaled or not,
    and scales them if needed.
    """

    broker: Broker
    consumer_updates_coordinator: Optional[ConsumerUpdatesCoordinator]
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
        """
        Updates the configuration of the coordinator.
        """
        config_reader = ConfigParser(storage=self.storage)

        if not config_reader.config:
            self.consumer_updates_coordinator = None
            return

        self.consumer_updates_coordinator = ConsumerUpdatesCoordinator(
            config=config_reader.config.coordinator_config, storage=self.storage
        )

    def run(self):
        """
        Checks if the configuration has changed, and scales the consumers if needed.
        """
        message = self.subscription.get_message()
        if message:
            LOGGER.info('Updating configuration.')
            self.update_configuration()

        self.scale()

    def scale(self):
        """
        Scales the consumers, if needed.
        """
        if not self.consumer_updates_coordinator:
            return

        for (app, app_config) in self.consumer_updates_coordinator.config.apps.items():
            if app_config.mode == AppMode.NOOP:
                continue

            queues_config = app_config.queues

            broker_uri = self.infrastructure_provider.broker_uri(app)

            try:
                stats = self.broker.stats(broker_uri)
                queues = self.broker.queues(queues_config.keys(), stats)
            except BrokerError:
                return

            updates = dict()
            for queue in queues:
                (
                    new_consumer_count,
                    consumer_formation,
                ) = self.consumer_updates_coordinator.compute_consumers_count(
                    app, app_config.mode, queue
                )

                if new_consumer_count is None:
                    continue

                updates[consumer_formation] = new_consumer_count

            if not updates:
                continue

            try:
                self.infrastructure_provider.scale(app, updates)
            except InfrastructureProviderError:
                pass

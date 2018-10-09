import threading

import structlog

from rectifier.balancer import Balancer
from rectifier.infrastructure_provider import InfrastructureProvider
from rectifier.message_brokers import Broker

LOGGER = structlog.get_logger(__name__)


class Monitor:
    def __init__(self, broker: Broker, infrastructure_provider: InfrastructureProvider, balancer: Balancer) -> None:
        self.broker = broker
        self.infrastructure_provider = infrastructure_provider
        self.balancer = balancer

        self._should_stop = threading.Event()

    def stop(self) -> None:
        self._should_stop.set()

    def scale(self):
        queues = self.broker.queues(self.balancer.config.queues.keys())

        for queue in queues:
            new_consumer_count = self.balancer.compute_consumers_count(queue)
            if new_consumer_count is None:
                continue

            self.infrastructure_provider.scale(queue.queue_name, new_consumer_count)

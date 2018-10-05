from datetime import datetime

import structlog

from rectifier.config import BalancerConfig
from rectifier.queue import Queue

LOGGER = structlog.get_logger(__name__)


class Balancer:
    def __init__(self, config: BalancerConfig):
        self.config = config

        self.queues_update_time = dict()

    def compute_consumers_count(self, queue: Queue):
        LOGGER.info("Computing queue", queue=queue)

        last_update = self.queues_update_time.get(queue.queue_name)

        queue_config = self.config.queues[queue.queue_name]

        if last_update is not None:
            time_since_update = datetime.now() - last_update
            if time_since_update.seconds < queue_config.cooldown:
                LOGGER.info(
                    "Not updating the queue yet",
                    last_update=last_update,
                    cooldown=queue_config.cooldown,
                    timedelta=time_since_update.seconds)
                return None

        matching_interval_index = [
            i for (i, messages_count) in enumerate(queue_config.intervals)
            if queue.messages >= messages_count
        ][-1]

        consumers_for_interval = queue_config.workers[matching_interval_index]

        if queue.consumers_count == consumers_for_interval:
            LOGGER.info(
                "Nothing to do. Queue has the proper consumer count.",
                consumer_cont=queue.consumers_count)
            return None

        self.queues_update_time[queue.queue_name] = datetime.now()
        return consumers_for_interval

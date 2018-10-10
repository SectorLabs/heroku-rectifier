import pickle
from datetime import datetime
from json import JSONDecodeError
from typing import Dict, Optional

import structlog

from rectifier.config import CoordinatorConfig
from rectifier.queue import Queue
from rectifier.storage import Storage
from rectifier import settings

LOGGER = structlog.get_logger(__name__)


class ConsumerUpdatesCoordinator:
    """
    Keeps track of the updates time of the queues, storing/loading them from the storage.

    Computes the count of the consumers which should be used for a given queue.
    """

    queues_update_time: Dict[str, datetime]

    def __init__(self, config: CoordinatorConfig, storage: Storage) -> None:
        """
        :param config: The configuration to be used for computing the number of consumers.
        :param storage: The storage for storing/loading the update times.
        """
        self.config = config
        self.storage = storage

        update_times = storage.get(settings.REDIS_UPDATE_TIMES)
        if update_times is None:
            self.queues_update_time = dict()
            return

        try:
            self.queues_update_time = pickle.loads(update_times)
            return
        except (JSONDecodeError, TypeError):
            LOGGER.info(
                'Failed to parse the update times from the redis store.',
                queues_update_time=update_times,
            )

        self.queues_update_time = dict()

    def _update_time(self, queue_name: str) -> None:
        """
        Updates the time of update for a given queue name, both in memory and in the persistent storage.
        :param queue_name: The name of the queue to be updated.
        """
        time_of_update = datetime.now()

        self.queues_update_time[queue_name] = time_of_update
        self.storage.set(
            settings.REDIS_UPDATE_TIMES, pickle.dumps(self.queues_update_time)
        )

    def compute_consumers_count(self, queue: Queue) -> Optional[int]:
        """
        Computes the count of the consumers which should be used for a queue, given its stats and the configuration.

        :param queue: The queue for which the consumers count should be calculated.
        :return:
            None
                - if no update should be made (either because the cooldown hasn't yet expired, or the queue
                already has the proper number of consumers).

            Otherwise
                - the number of consumers which should be used for this queue.
        """
        LOGGER.info("Computing the consumers count.", queue=queue)

        last_update = self.queues_update_time.get(queue.queue_name)

        queue_config = self.config.queues[queue.queue_name]

        if last_update is not None:
            time_since_update = datetime.now() - last_update
            if time_since_update.seconds < queue_config.cooldown:
                LOGGER.info(
                    "Not updating the queue yet.",
                    last_update=last_update,
                    cooldown=queue_config.cooldown,
                    timedelta=time_since_update.seconds,
                )
                return None

        matching_interval_index = [
            i
            for (i, messages_count) in enumerate(queue_config.intervals)
            if queue.messages >= messages_count
        ][-1]

        consumers_for_interval = queue_config.workers[matching_interval_index]

        if queue.consumers_count == consumers_for_interval:
            LOGGER.info(
                "Nothing to do. Queue has the proper consumer count.",
                consumer_cont=queue.consumers_count,
            )
            return None

        self._update_time(queue.queue_name)
        return consumers_for_interval
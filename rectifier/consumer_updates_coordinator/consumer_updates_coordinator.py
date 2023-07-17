import pickle
from collections import defaultdict
from datetime import datetime
from json import JSONDecodeError
from typing import DefaultDict, Dict, Optional, Tuple

import structlog

from rectifier.config import CoordinatorConfig, AppMode
from rectifier.queue import Queue
from rectifier.storage import Storage
from rectifier import settings

LOGGER = structlog.get_logger(__name__)


class ConsumerUpdatesCoordinator:
    """
    Keeps track of the updates time of the queues, storing/loading them from the storage.

    Computes the count of the consumers which should be used for a given queue.
    """

    queues_update_time: DefaultDict[str, Dict[str, datetime]]

    def __init__(self, config: CoordinatorConfig, storage: Storage) -> None:
        """
        :param config: The configuration to be used for computing the number of consumers.
        :param storage: The storage for storing/loading the update times.
        """
        self.config = config
        self.storage = storage

        update_times = storage.get(settings.REDIS_UPDATE_TIMES)
        if update_times is None:
            self.queues_update_time = defaultdict(dict)
            return

        try:
            self.queues_update_time = pickle.loads(update_times)
            return
        except (JSONDecodeError, TypeError):
            LOGGER.info(
                'Failed to parse the update times from the redis store.',
                queues_update_time=update_times,
            )

        self.queues_update_time = defaultdict(dict)

    def _update_time(self, app_name: str, queue_name: str) -> None:
        """
        Updates the time of update for a given queue name, both in memory and in the persistent storage.
        :param queue_name: The name of the queue to be updated.
        """
        time_of_update = datetime.now()

        self.queues_update_time[app_name][queue_name] = time_of_update
        self.storage.set(
            settings.REDIS_UPDATE_TIMES, pickle.dumps(self.queues_update_time)
        )

    def compute_consumers_count(
        self, app: str, app_mode: AppMode, queue: Queue
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Computes the count of the consumers which should be used for a queue, given its stats and the configuration.

        :param app: The app in which the queue resides.
        :param app_mode: The mode in which the current app is set to run
        :param queue: The queue for which the consumers count should be calculated.
        :return:
            None
                - if no update should be made (either because the cooldown hasn't yet expired, or the queue
                already has the proper number of consumers).

            Otherwise
                - the number of consumers which should be used for this queue.
        """
        last_update = self.queues_update_time[app].get(queue.queue_name)

        queue_config = self.config.apps[app].queues[queue.queue_name]

        if last_update is not None:
            time_since_update = datetime.now() - last_update
            if time_since_update.seconds < queue_config.cooldown:
                LOGGER.info(
                    "Not updating the queues yet.",
                    app=app,
                    queue_name=queue.queue_name,
                    last_update=last_update.isoformat(),
                    cooldown=queue_config.cooldown,
                    timedelta=time_since_update.seconds,
                )
                return None, None

        if app_mode == AppMode.KILL:
            return (
                0 if queue.consumers_count else None,
                queue_config.consumers_formation_name,
            )

        matching_interval_index = [
            i
            for (i, messages_count) in enumerate(queue_config.intervals)
            if queue.messages >= messages_count
        ][-1]

        consumers_for_interval = queue_config.workers[matching_interval_index]

        if queue.consumers_count == consumers_for_interval:
            return None, None

        self._update_time(app, queue.queue_name)
        return consumers_for_interval, queue_config.consumers_formation_name

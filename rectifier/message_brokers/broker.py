from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from rectifier.queue import Queue


class Broker(ABC):
    """
    A message broker in which queues exist. Able to retrieve stats about the queues in real time.
    """

    @abstractmethod
    def stats(self):
        """Retrieves all the available queues stats"""

    @abstractmethod
    def queues(
        self, queue_names: List[str], stats: Optional[Dict] = None
    ) -> List[Queue]:
        """Returns the stats for the given queue names, in a proper representation."""

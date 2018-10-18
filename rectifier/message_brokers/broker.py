from abc import ABC, abstractmethod
from typing import List, Dict

from rectifier.queue import Queue


class Broker(ABC):
    """
    A message broker in which queues exist. Able to retrieve stats about the queues in real time.
    """

    @staticmethod
    @abstractmethod
    def stats(uri: str):
        """Retrieves all the available queues stats"""

    @staticmethod
    @abstractmethod
    def queues(interest_queues: List[str], stats: Dict) -> List[Queue]:
        """Returns the stats for the given queue names, in a proper representation."""

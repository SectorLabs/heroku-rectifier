from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from rectifier.queue import Queue


class Broker(ABC):
    @abstractmethod
    def stats(self):
        pass

    @abstractmethod
    def queues(self, queue_names: List[str], stats: Optional[Dict] = None) -> List[Queue]:
        pass


from dataclasses import dataclass
from typing import List, Dict


@dataclass
class QueueConfig:
    """Configuration for a single Queue"""

    intervals: List[int]
    workers: List[int]
    cooldown: int
    queue_name: str


@dataclass
class CoordinatorConfig:
    """Configuration for the coordinator."""

    queues: Dict[str, QueueConfig]


@dataclass
class Config:
    """Configuration for the auto-scaler."""

    coordinator_config: CoordinatorConfig


__all__ = ['QueueConfig', 'CoordinatorConfig', 'Config']

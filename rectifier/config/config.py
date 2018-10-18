from dataclasses import dataclass
from typing import List, Dict


@dataclass
class QueueConfig:
    """Configuration for a single Queue"""

    intervals: List[int]
    workers: List[int]
    cooldown: int
    queue_name: str
    consumers_formation_name: str


@dataclass
class AppConfig:
    """Configuration for the coordinator."""

    queues: Dict[str, QueueConfig]


@dataclass
class CoordinatorConfig:
    apps: Dict[str, AppConfig]


@dataclass
class Config:
    """Configuration for the auto-scaler."""

    coordinator_config: CoordinatorConfig


__all__ = ['QueueConfig', 'CoordinatorConfig', 'AppConfig', 'Config']

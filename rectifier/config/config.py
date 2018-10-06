from dataclasses import dataclass
from typing import List, Dict


@dataclass
class RabbitMQConfig:
    """Configuration for RabbitMQ."""

    host: str
    port: int
    vhost: str
    user: str
    password: str
    secure: bool = False


@dataclass
class QueueConfig:
    """Configuration for a single Queue"""

    intervals: List[int]
    workers: List[int]
    cooldown: int
    queue_name: str


@dataclass
class BalancerConfig:
    """Configuration for a single balancer."""
    queues: Dict[str, QueueConfig]


@dataclass
class Config:
    """Configuration for the auto-scaler."""

    rabbitMQ_config: RabbitMQConfig
    balancer_config: BalancerConfig


__all__ = ['RabbitMQConfig', 'QueueConfig', 'BalancerConfig', 'Config']
from dataclasses import dataclass


@dataclass
class Queue:
    queue_name: str
    consumers_count: int
    messages: int



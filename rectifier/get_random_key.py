from typing import List, Optional
import random


def get_random_key(keys: List[str]) -> Optional[str]:
    if not keys:
        return None

    return random.choice(keys)

class Config:
    QUEUE = {
        'type': 'object',
        'properties': {
            'intervals': {'type': 'array', 'items': {'type': 'number'}},
            'workers': {'type': 'array', 'items': {'type': 'number'}},
            'cooldown': {'type': 'number'},
        },
        'required': ['intervals', 'workers', 'cooldown'],
    }

    SCHEMA = {
        'type': 'object',
        'properties': {
            'queues': {'type': 'object', 'patternProperties': {".*": QUEUE}}
        },
        'required': ['queues'],
    }


__all__ = ['Config']

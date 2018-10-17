class Config:
    QUEUE = {
        'type': 'object',
        'properties': {
            'intervals': {'type': 'array', 'items': {'type': 'number'}},
            'workers': {'type': 'array', 'items': {'type': 'number'}},
            'cooldown': {'type': 'number'},
            'consumers_formation_name': {'type': 'string'},
        },
        'required': ['intervals', 'workers', 'cooldown', 'consumers_formation_name'],
    }

    SCHEMA = {
        'type': 'object',
        'properties': {
            'queues': {'type': 'object', 'patternProperties': {".*": QUEUE}}
        },
        'required': ['queues'],
    }


__all__ = ['Config']

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
        'additionalProperties': False,
    }

    APP = {
        'type': 'object',
        'patternProperties': {
            '^(?!mode).*$': QUEUE,
            '^mode$': {'type': 'string', 'enum': ['scale', 'noop', 'kill']},
        },
    }

    SCHEMA = {
        'type': 'object',
        'patternProperties': {'.*': APP},
        'additionalProperties': False,
    }


__all__ = ['Config']

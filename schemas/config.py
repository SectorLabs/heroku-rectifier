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

    APP = {'type': 'object', 'patternProperties': {'.*': QUEUE}}

    SCHEMA = {'type': 'object', 'pattern_properties': {'.*': APP}}


__all__ = ['Config']

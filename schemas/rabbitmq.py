class RabbitMQ:
    QUEUE = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'messages': {'type': 'integer'},
            'consumers': {'type': 'integer'}
        },
        'required': ['name'],
    }

    SCHEMA = {'type': 'array', 'items': QUEUE}


__all__ = ['RabbitMQ']

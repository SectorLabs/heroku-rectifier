class RabbitMQ:
    QUEUE = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'messages': {'type': 'integer'},
            'consumers': {'type': 'integer'},
        },
        'required': ['name', 'messages', 'consumers'],
    }

    SCHEMA = {'type': 'array', 'items': QUEUE}


__all__ = ['RabbitMQ']

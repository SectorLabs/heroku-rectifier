class Config:
    RABBIT_MQ = {
        'type': 'object',
        'properties': {
            'host': {
                'type': 'string'
            },
            'port': {
                'type': 'integer'
            },
            'vhost': {
                'type': 'string'
            },
            'user': {
                'type': 'string'
            },
            'password': {
                'type': 'string'
            },
            'secure': {
                'type': 'boolean'
            },
        },
        'required': ['host', 'vhost', 'user', 'password', 'secure']
    }

    QUEUE = {
        'type': 'object',
        'properties': {
            'intervals': {
                'type': 'array',
                'items': {
                    'type': 'number'
                }
            },
            'workers': {
                'type': 'array',
                'items': {
                    'type': 'number',
                }
            },
            'check_interval': {
                'type': 'number',
            }
        },
        'required': ['intervals', 'workers', 'check_interval']
    }

    SCHEMA = {
        'type': 'object',
        'properties': {
            'rabbitMQ': RABBIT_MQ,
            'queues': {
                'type': 'object',
                'items': {
                    'type': 'object',
                    'items': QUEUE
                }
            }
        },
        'required': ['queues', 'rabbitMQ']
    }


__all__ = ['Config']

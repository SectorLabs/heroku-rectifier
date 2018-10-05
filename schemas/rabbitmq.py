class RabbitMQ(object):
    QUEUE = {
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string'
            },
            'messages': {
                'type': 'integer'
            },
            'message_stats': {
                'type': 'object',
                'properties': {
                    'ack_details': {
                        'type': 'object',
                        'properties': {
                            'rate': {
                                'type': 'number'
                            }
                        },
                        'required': ['rate']
                    }
                },
                # 'required': ['ack_details']
            }
        },
        'required': ['name', 'messages']
    }

    SCHEMA = {'type': 'array', 'items': QUEUE}


__all__ = ['RabbitMQ']

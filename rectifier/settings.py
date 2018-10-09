from environs import Env

env = Env()

REDIS_CHANNEL = 'config'
REDIS_CONFIG_KEY = 'config'
REDIS_UPDATE_TIMES = 'update_times'

REDIS = {
    'host': env('REDIS_HOST', 'localhost'),
    'port': env.int('REDIS_PORT', 6379),
    'db': env('REDIS_DB', '0'),
    'password': env('REDIS_PASSWORD', None),
}

RABBIT_MQ = {
    'host': env('RABBIT_MQ_HOST', '127.0.0.1'),
    'port': env.int('RABBIT_MQ_PORT', 15672),
    'user': env('RABBIT_MQ_USER', 'guest'),
    'password': env('RABBIT_MQ_PASSWORD', 'guest'),
    'secure': env.bool('RABBIT_MQ_SECURE', False),
    'vhost': env('RABBIT_MQ_VHOST', ''),
}

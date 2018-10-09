from environs import Env

env = Env()

REDIS_CHANNEL = 'config'
REDIS_CONFIG_KEY = 'config'
REDIS_UPDATE_TIMES = 'update_times'

REDIS_URL = env('REDIS_URL', 'redis://127.0.0.1:6379/0')

RABBIT_MQ = {
    'host': env('RABBIT_MQ_HOST', '127.0.0.1:15672'),
    'user': env('RABBIT_MQ_USER', 'guest'),
    'password': env('RABBIT_MQ_PASSWORD', 'guest'),
    'secure': env.bool('RABBIT_MQ_SECURE', False),
    'vhost': env('RABBIT_MQ_VHOST', ''),
}

SECRET_KEY = env('SECRET_KEY', 'my-great-secret-key')
TIME_BETWEEN_REQUESTS = env.int('TIME_BETWEEN_REQUESTS', 30)

HEROKU_API_KEY = env('HEROKU_API_KEY', None)
HEROKU_APP_NAME = env('HEROKU_APP_NAME', None)

HOST = env('HOST', '0.0.0.0')
PORT = env.int('PORT', 80)

BASIC_AUTH_USER = env('BASIC_AUTH_USER', 'guest')
BASIC_AUTH_PASSWORD = env('BASIC_AUTH_PASSWORD', 'guest')

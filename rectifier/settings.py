from environs import Env

env = Env()

REDIS_CHANNEL = 'config'
REDIS_CONFIG_KEY = 'config'
REDIS_UPDATE_TIMES = 'update_times'

BROKER_URL_KEY = 'CLOUDAMQP_URL'

REDIS_URL = env('REDIS_URL', 'redis://127.0.0.1:6379/0')

RABBIT_MQ_SECURE = env.bool('RABBIT_MQ_SECURE', False)

SECRET_KEY = env('SECRET_KEY', 'my-great-secret-key')
TIME_BETWEEN_REQUESTS = env.int('TIME_BETWEEN_REQUESTS', 30)

HEROKU_API_KEY = env('HEROKU_API_KEY', None)

HOST = env('HOST', '0.0.0.0')
PORT = env.int('PORT', 80)

BASIC_AUTH_USER = env('BASIC_AUTH_USER', 'guest')
BASIC_AUTH_PASSWORD = env('BASIC_AUTH_PASSWORD', 'guest')

DRY_RUN = env.bool('DRY_RUN', False)

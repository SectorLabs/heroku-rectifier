from environs import Env
import structlog
from logging.config import dictConfig


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
HEROKU_API_KEYS = env.list(
    'HEROKU_API_KEYS', [HEROKU_API_KEY] if HEROKU_API_KEY else []
)

HOST = env('HOST', '0.0.0.0')
PORT = env.int('PORT', 80)

BASIC_AUTH_USER = env('BASIC_AUTH_USER', 'guest')
BASIC_AUTH_PASSWORD = env('BASIC_AUTH_PASSWORD', 'guest')

DRY_RUN = env.bool('DRY_RUN', False)

HEALTH_CHECKER_FAILED_STATUS = env('HEALTH_CHECKER_FAILED_STATUS', 503)

timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    timestamper,
]

dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(colors=True),
                'format': '%(message)s',
                'foreign_pre_chain': pre_chain,
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            }
        },
        'loggers': {
            'rectifier': {'level': 'INFO', 'handlers': ['console'], 'propagate': False}
        },
    }
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(sort_keys=True),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

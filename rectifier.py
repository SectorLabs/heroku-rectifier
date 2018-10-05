import time

import structlog

from rectifier.balancer.balancer import Balancer
from rectifier.config.config_reader import ConfigReader
from rectifier.infrastructure_provider.heroku import Heroku
from rectifier.message_brokers.rabbitmq import RabbitMQ
from rectifier.monitors.monitor import Monitor

LOGGER = structlog.get_logger(__name__)

config = ConfigReader.from_file('config.json')

rabbitMQ = RabbitMQ(config=config.rabbitMQ_config)
balancer = Balancer(config=config.balancer_config)
heroku = Heroku()
monitor = Monitor(
    broker=rabbitMQ, infrastructure_provider=heroku, balancer=balancer)

monitor.start_monitoring()

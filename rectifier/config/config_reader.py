import json
from typing import Dict

import jsonschema
import structlog

import schemas
from rectifier.config import Config, RabbitMQConfig, BalancerConfig, QueueConfig

LOGGER = structlog.get_logger(__name__)


class ConfigReadError(RuntimeError):
    """Error that occurs while reading
    the configuration."""

    pass


class ConfigReader:

    @classmethod
    def from_file(cls, filename: str) -> Config:
        """Reads the configuration from the specified JSON file."""

        errors = (
            EOFError, MemoryError, OSError, UnicodeError, IOError,
            EnvironmentError, TypeError, ValueError, OverflowError,
            json.JSONDecodeError
        )

        try:
            with open(filename, 'r') as fp:
                data = json.loads(fp.read())
        except errors as err:
            message = 'Failed to read config from \'%s\'' % filename
            LOGGER.error(message, filename=filename, err=err)
            raise ConfigReadError(message) from err

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict) -> Config:
        """Reads the configuration from the specified dictionary."""

        cls.validate(data)

        queues_config = data.get('queues', [])
        rabbit_mq_config = data.get('rabbitMQ', {})

        return Config(
            rabbitMQ_config=cls.rabbitmq_config_from_dict(rabbit_mq_config),
            balancer_config=cls.balancer_config_from_dict(queues_config)
        )

    @classmethod
    def rabbitmq_config_from_dict(cls, data: Dict) -> RabbitMQConfig:
        return RabbitMQConfig(
            host=data['host'],
            port=data['port'],
            user=data['user'],
            password=data['password'],
            secure=data['secure'],
            vhost=data['vhost'],
        )

    @classmethod
    def balancer_config_from_dict(cls, data: Dict) -> BalancerConfig:
        queues = dict()
        for (queue_name, queue_properties) in data.items():
            intervals = queue_properties['intervals']
            workers = queue_properties['workers']
            cooldown = queue_properties['cooldown']

            if len(intervals) != len(workers):
                message = 'The length of the intervals array should match the length of the workers array.'
                LOGGER.error(message, queue_name=queue_name)
                raise ConfigReadError(message)

            if intervals[0] != 0:
                message = 'The first interval should start with 0'
                LOGGER.error(message, intervals=intervals, queue_name=queue_name)
                raise ConfigReadError(message)

            if any([interval < 0 for interval in intervals]):
                message = 'The entries in the message intervals should all be positive'
                LOGGER.error(message, intervals=intervals, queue_name=queue_name)
                raise ConfigReadError(message)

            if any([worker < 0 for worker in workers]):
                message = 'The entries in the workers count array should all be positive'
                LOGGER.error(message, workers=workers, queue_name=queue_name)
                raise ConfigReadError(message)

            if cooldown < 0:
                message = 'The cooldown should be positive'
                LOGGER.error(message, cooldown=cooldown, queue_name=queue_name)
                raise ConfigReadError(message)

            if sorted(intervals) != intervals:
                message = 'The intervals should be sorted in ascending order'
                LOGGER.error(message, intervals=intervals, queue_name=queue_name)
                raise ConfigReadError(message)

            queues[queue_name] = QueueConfig(queue_name=queue_name, **queue_properties)

        return BalancerConfig(
            queues=queues
        )

    @classmethod
    def validate(cls, data: Dict) -> None:
        """Validates the specified raw configuration.

        Raises:
            ConfigReadError:
                When the configuration does not match
                the schema.
        """

        try:
            jsonschema.validate(data, schemas.Config.SCHEMA)
        except jsonschema.ValidationError as err:
            message = 'Failed to validate configuration'
            LOGGER.error(message, config=data, err=err)
            raise ConfigReadError(message) from err

import json
from json import JSONDecodeError
from typing import Dict

import jsonschema
import structlog

import schemas
from rectifier.config import Config, AppConfig, QueueConfig, CoordinatorConfig
from rectifier.storage.storage import Storage
from rectifier import settings

LOGGER = structlog.get_logger(__name__)


class ConfigReadError(RuntimeError):
    """Error that occurs while reading
    the configuration."""

    pass


class ConfigParser:
    """A utility class for parsing and validating configuration."""

    def __init__(self, storage: Storage) -> None:
        """Takes the configuration from the storage, and tries to parse it."""

        storage_config = storage.get(settings.REDIS_CONFIG_KEY)
        config_dict = None

        if storage_config is None:
            LOGGER.info('No configuration found in the storage.')
        else:
            try:
                config_dict = json.loads(storage_config)
            except (JSONDecodeError, TypeError):
                LOGGER.info(
                    'Failed to parse the storage configuration.', config=storage_config
                )

        self.raw_config = config_dict
        self.config = ConfigParser.from_dict(config_dict) if config_dict else None
        LOGGER.info('Using configuration:', config=self.config)

    @classmethod
    def from_dict(cls, data: Dict) -> Config:
        """Reads the configuration from the specified dictionary."""
        cls.validate(data)

        apps = dict()
        for (app, queues_config) in data.items():
            queues = dict()

            for (queue_name, queue_properties) in queues_config.items():
                queues[queue_name] = QueueConfig(
                    queue_name=queue_name, **queue_properties
                )

            apps[app] = AppConfig(queues=queues)

        return Config(coordinator_config=CoordinatorConfig(apps=apps))

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
            message = 'Failed to validate configuration.'
            LOGGER.error(message, config=data, err=err)
            raise ConfigReadError(message) from err

        for (app, queues) in data.items():
            for (queue_name, queue_properties) in queues.items():
                intervals = queue_properties['intervals']
                workers = queue_properties['workers']
                cooldown = queue_properties['cooldown']

                if len(intervals) != len(workers):
                    message = 'The length of the intervals array should match the length of the workers array.'
                    LOGGER.error(message, queue_name=queue_name)
                    raise ConfigReadError(message)

                if intervals[0] != 0:
                    message = 'The first interval should start with 0.'
                    LOGGER.error(message, intervals=intervals, queue_name=queue_name)
                    raise ConfigReadError(message)

                if any([interval < 0 for interval in intervals]):
                    message = (
                        'The entries in the message intervals should all be positive.'
                    )
                    LOGGER.error(message, intervals=intervals, queue_name=queue_name)
                    raise ConfigReadError(message)

                if any([worker < 0 for worker in workers]):
                    message = (
                        'The entries in the workers count array should all be positive.'
                    )
                    LOGGER.error(message, workers=workers, queue_name=queue_name)
                    raise ConfigReadError(message)

                if cooldown < 0:
                    message = 'The cooldown should be positive.'
                    LOGGER.error(message, cooldown=cooldown, queue_name=queue_name)
                    raise ConfigReadError(message)

                if sorted(intervals) != intervals:
                    message = 'The intervals should be sorted in ascending order.'
                    LOGGER.error(message, intervals=intervals, queue_name=queue_name)
                    raise ConfigReadError(message)

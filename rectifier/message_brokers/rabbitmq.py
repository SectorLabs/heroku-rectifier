import json
from typing import Optional, Dict, List

import jsonschema as jsonschema
import requests
import structlog

import schemas
from rectifier.queue import Queue
from rectifier import settings
from .broker import Broker

LOGGER = structlog.get_logger(__name__)


class BrokerError(RuntimeError):
    """Error thrown when something goes
    wrong when retrieving the load from
    the backpressure implementation."""
    pass


class RabbitMQ(Broker):
    def __init__(self) -> None:
        self.config = settings.RABBIT_MQ

    def stats(self):
        """Gets a list of available queues and stat information
        for each available queue."""

        host = self.config.get('host')
        port = self.config.get('port')
        vhost = self.config.get('vhost')
        user = self.config.get('user')
        password = self.config.get('password')
        protocol = 'https' if self.config.get('secure') else 'http'

        url = '%s://%s:%d/api/queues/%s' % (protocol, host, port, vhost)

        auth = requests.auth.HTTPBasicAuth(user, password)

        errors = (
            requests.exceptions.RequestException, requests.exceptions.HTTPError,
            EOFError, MemoryError, OSError, UnicodeError, IOError,
            EnvironmentError, TypeError, ValueError, OverflowError,
            json.JSONDecodeError
        )

        LOGGER.debug('Making request to RabbitMQ', url=url)

        try:
            response = requests.get(url, auth=auth)
            response.raise_for_status()
        except errors as err:
            message = 'Could not retrieve queue stats from RabbitMQ'
            LOGGER.error(message, url=url, err=err)
            raise BrokerError(message) from err

        try:
            data = response.json()
        except errors as err:
            message = 'Could not decode queue stats from RabbitMQ'
            LOGGER.error(message, url=url, err=err, response=response.content)
            raise BrokerError(message) from err

        try:
            jsonschema.validate(data, schemas.RabbitMQ.SCHEMA)
        except jsonschema.ValidationError as err:
            message = 'Could not validate queue stats returned by RabbitMQ'
            LOGGER.error(message, url=url, err=err, data=data)
            raise BrokerError(message) from err

        return data

    def queues(self, queue_names: List[str], stats: Optional[Dict] = None) -> List[Queue]:
        if stats is None:
            stats = self.stats()

        queues = []

        for queue_name in queue_names:
            queue_list = list(filter(lambda queue_stats: queue_stats['name'] == queue_name, stats))

            if len(queue_list) != 1:
                message = 'Could not find such a queue name'
                LOGGER.error(message, response=stats, queue_name=queue_name)
                raise BrokerError(message)

            queue = queue_list[0]

            queues.append(Queue(
                queue_name=queue_name,
                consumers_count=queue.get('consumers'),
                messages=queue.get('messages')
            ))

        return queues

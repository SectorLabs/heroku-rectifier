import json
from typing import Dict, List

import jsonschema as jsonschema
import requests
import structlog
import pika

import schemas
from rectifier import settings
from rectifier.queue import Queue
from .broker import Broker

LOGGER = structlog.get_logger(__name__)


class BrokerError(RuntimeError):
    """Error thrown when something goes
    wrong when retrieving the load from
    the Broker implementation."""

    pass


class RabbitMQ(Broker):
    """
    An wrapper over RabbitMQ. Can fetch data about the queues in real time.
    """

    @staticmethod
    def stats(uri: str):
        """Gets a list of available queues and stat information
        for each available queue."""

        url_params = pika.URLParameters(uri)

        host = url_params.host
        if url_params.port and url_params.port != url_params.DEFAULT_PORT:
            host = '%s:%s' % (host, url_params.port)
        user = url_params.credentials.username
        password = url_params.credentials.password
        vhost = url_params.virtual_host

        protocol = 'https' if settings.RABBIT_MQ_SECURE else 'http'
        url = '%s://%s/api/queues/%s' % (protocol, host, vhost)

        auth = requests.auth.HTTPBasicAuth(user, password)

        errors = (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
            EOFError,
            MemoryError,
            OSError,
            UnicodeError,
            IOError,
            EnvironmentError,
            TypeError,
            ValueError,
            OverflowError,
            json.JSONDecodeError,
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

    @staticmethod
    def queues(interest_queues: List[str], stats: Dict) -> List[Queue]:
        queues = []

        for queue_name in interest_queues:
            queue_list = list(
                filter(lambda queue_stats: queue_stats['name'] == queue_name, stats)
            )

            if len(queue_list) != 1:
                message = 'Could not find such a queue name'
                LOGGER.error(message, response=stats, queue_name=queue_name)
                raise BrokerError(message)

            queue = queue_list[0]

            queues.append(
                Queue(
                    queue_name=queue_name,
                    consumers_count=queue.get('consumers'),
                    messages=queue.get('messages'),
                )
            )

        return queues

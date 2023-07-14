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

    @classmethod
    def queues(cls, interest_queues: List[str], stats: Dict) -> List[Queue]:
        multiple_queues_config = cls._multiple_queue_configs(interest_queues)
        single_queue_configs = cls._single_queue_configs(interest_queues)

        queues = []
        for queue_name in single_queue_configs:
            queue = cls._handle_single_queue_config(stats, queue_name)
            if queue:
                queues.append(queue)

        for queue_names in multiple_queues_config:
            queue = cls._handle_multiple_queues_config(stats, queue_names)
            if queue:
                queues.append(queue)

        return queues

    @classmethod
    def _handle_single_queue_config(cls, stats: Dict, queue_name: str):
        queue_list = cls._filter_stats(stats, [queue_name])

        if len(queue_list) != 1:
            message = 'Could not find such a queue name'
            LOGGER.error(message, response=stats, queue_name=queue_name)
            return

        queue = queue_list[0]
        return Queue(
            queue_name=queue_name,
            consumers_count=queue.get('consumers'),
            messages=queue.get('messages'),
        )

    @classmethod
    def _handle_multiple_queues_config(cls, stats: Dict, raw_queue_names: str):
        queue_names = list(map(str.strip, raw_queue_names.split('+')))
        queue_list = cls._filter_stats(stats, queue_names)

        if len(queue_list) != len(queue_names):
            message = 'Could not find all queues'
            LOGGER.error(message, response=stats, queue_names=queue_names)
            return

        expected_consumers_count = queue_list[0].get('consumers')
        for idx, queue in enumerate(queue_list[1:]):
            consumer_count = queue.get('consumers')
            queue_name = queue_names[idx + 1]

            if consumer_count != expected_consumers_count:
                LOGGER.error(
                    "Missmatching consumer count",
                    queue_name=queue_name,
                    count=[consumer_count, expected_consumers_count],
                )
                return

        return Queue(
            queue_name="+".join(queue_names),
            consumers_count=queue_list[0].get('consumers'),
            messages=sum(q.get('messages') for q in queue_list),
        )

    @staticmethod
    def _single_queue_configs(interest_queues: List[str]) -> List[str]:
        return [
            interest_queue
            for interest_queue in interest_queues
            if "+" not in interest_queue
        ]

    @staticmethod
    def _multiple_queue_configs(interest_queues: List[str]) -> List[str]:
        return [
            interest_queue
            for interest_queue in interest_queues
            if "+" in interest_queue
        ]

    @staticmethod
    def _filter_stats(stats: Dict, queue_names: List[str]):
        return list(
            filter(lambda queue_stats: queue_stats['name'] in queue_names, stats)
        )

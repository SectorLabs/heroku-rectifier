import asyncio
import json
import threading
from collections import defaultdict
from typing import Dict, List, Optional

import flask
from werkzeug.serving import make_server


class RabbitMQAPIMockVHost(object):
    """Mocked data that the mock returns."""

    _queues: Dict[str, Dict]

    def __init__(self) -> None:
        self._queues = {}

    def set_queue(self, name: str, consumers: int = 0, messages: int = 0) -> None:
        """Creates or updates the queue with then specified name.

        Arguments:
            name:
                The name of the queue to create or update.

            messages:
                Total amount of messages in the queue.

            consumers:
                The amount of the consumers in the queue.
        """
        self._queues[name] = {'messages': messages, 'consumers': consumers}

    def set_queue_messages(self, name: str, messages: int) -> None:
        """Sets the amount of messages currently in the queue."""

        queue = self._get_queue(name)
        queue['messages'] = messages

    def delete_queue(self, name: str) -> None:
        """Deletes the queues with the specified name."""

        del self._queues[name]

    def get_queues(self) -> List[Dict]:
        """Gets a list of all queues in the format
        that the RabbitMQ API would return them in."""

        return [
            {
                'name': queue_name,
                'messages': queue['messages'],
                'consumers': queue['consumers'],
            }
            for queue_name, queue in self._queues.items()
        ]

    def _get_queue(self, name: str) -> dict:
        """Gets the queue with then specified name.

        Raises:
            NameError:
                If no queue with the specified name
                exists.
        """

        queue = self._queues.get(name)
        if not queue:
            raise NameError('No such queue exist.')

        return queue


class RabbitMQAPIMock:
    """A mock for the RabbitmQ API.

    This starts a HTTP server that replies
    exactly like the RabbitMQ management
    API would."""

    vhosts: Dict

    def __init__(self) -> None:
        """Initializes a new instance of :see:RabbitMQAPIMock."""

        self.vhosts = defaultdict(RabbitMQAPIMockVHost)

        self._thread = threading.Thread(target=self._run)

        self._app = flask.Flask(__name__)
        self._app.add_url_rule(
            '/api/queues/<vhost_name>', 'queues', view_func=self._get_queues
        )
        self._server = make_server('127.0.0.1', 0, self._app)

        self.host = self._server.host
        self.port = self._server.port

    def start(self) -> None:
        """Starts the web server."""
        self._thread.start()

    def stop(self) -> None:
        """Stops the web server."""

        self._server.shutdown()
        self._thread.join(timeout=5000)

    def _run(self) -> None:
        """Entry-point for the server thread, actually
        runs the web server."""

        self._server.serve_forever()

    def _get_queues(self, vhost_name):
        """Gets an overview of all the queues, the amount
        of messages in them and the rate at which messages
        are being consumed."""

        vhost = self.vhosts.get(vhost_name)
        if not vhost:
            return flask.jsonify({'error': 'Object Not Found', 'reason': 'Not found'})

        return flask.jsonify(vhost.get_queues())

import threading
from collections import defaultdict
from typing import Dict

import flask
from werkzeug.serving import make_server


class RabbitMQAPIMock:
    """A mock for the RabbitmQ API.

    This starts a HTTP server that replies
    exactly like the RabbitMQ management
    API would."""

    _queues: Dict

    def __init__(self) -> None:
        """Initializes a new instance of :see:RabbitMQAPIMock."""

        self._queues = defaultdict(lambda: defaultdict(str))

        self._thread = threading.Thread(target=self._run)

        self._app = flask.Flask(__name__)
        self._app.add_url_rule(
            '/api/queues/<app_name>', 'queues', view_func=self._get_queues
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

    def _get_queues(self, app_name):
        """Gets an overview of all the queues, the amount
        of messages in them and the rate at which messages
        are being consumed."""

        queues = self._queues[app_name]
        return flask.jsonify(
            [
                {
                    'name': queue_name,
                    'messages': queue['messages'],
                    'consumers': queue['consumers'],
                }
                for queue_name, queue in queues.items()
            ]
        )

    def set_queue(
        self, app: str, name: str, consumers: int = 0, messages: int = 0
    ) -> None:
        """Creates or updates the queue with then specified name.

        Arguments:
            app:
                The app in which the queue resides

            name:
                The name of the queue to create or update.

            messages:
                Total amount of messages in the queue.

            consumers:
                The amount of the consumers in the queue.
        """
        self._queues[app][name] = {'messages': messages, 'consumers': consumers}

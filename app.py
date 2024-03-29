import os
import sys
import threading
import json
import time
import traceback
import errno

import structlog

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_basicauth import BasicAuth

from rectifier.config import ConfigParser, ConfigReadError
from rectifier.health_checker import HealthChecker
from rectifier.infrastructure_provider import Heroku
from rectifier.message_brokers import RabbitMQ
from rectifier.rectifier import Rectifier
from rectifier.storage.redis_storage import RedisStorage
from rectifier import settings

from schemas import Config

LOGGER = structlog.get_logger(__name__)

app = Flask(__name__)
app.secret_key = settings.SECRET_KEY

app.config['BASIC_AUTH_USERNAME'] = settings.BASIC_AUTH_USER
app.config['BASIC_AUTH_PASSWORD'] = settings.BASIC_AUTH_PASSWORD

basic_auth = BasicAuth(app)

storage = RedisStorage()
config_reader = ConfigParser(storage=storage)
health_checker = HealthChecker(storage)


class RectifierThread(threading.Thread):
    def run(self):
        rectifier = Rectifier(
            storage=RedisStorage(), broker=RabbitMQ(), infrastructure_provider=Heroku()
        )
        while True:
            rectifier.run()
            time.sleep(settings.TIME_BETWEEN_REQUESTS)


@app.route("/")
@basic_auth.required
def home():
    return render_template(
        'index.html',
        schema=Config.SCHEMA,
        config=json.dumps(config_reader.raw_config, indent=4),
    )


@app.route('/handle_data', methods=['POST'])
@basic_auth.required
def submit_configuration():
    config = request.form['code']
    try:
        ConfigParser.validate(json.loads(config))

        storage.set(settings.REDIS_CONFIG_KEY, config)
        storage.publish(settings.REDIS_CHANNEL, json.dumps(None))

        global config_reader
        config_reader = ConfigParser(storage=storage)

        flash('Succes!', 'info')
    except ConfigReadError as error:
        flash(str(error), 'error')

    return redirect(url_for('home'))


@app.route("/hc")
def health_check():
    return health_checker.run()


class WebThread(threading.Thread):
    def run(self):
        app.run()


def on_uncaught_exception(args):
    err_type, err_value, err_tb, thread = args
    sys.stderr.write("".join(traceback.format_exception(err_type, err_value, err_tb)))

    # do not replace with sys.exit(..), from docs, this quits
    # without waiting unlike sys.exit(..)
    # exit code must be EINTR for gunicorn to quit
    os._exit(errno.EINTR)


# unhandled exceptions raised in threads are caught
# by the hook and cause the whole process to exit
threading.excepthook = on_uncaught_exception  # type: ignore

rectifier = RectifierThread()
rectifier.start()


if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT)

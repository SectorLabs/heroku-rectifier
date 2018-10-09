import threading
import json
import time

from flask import Flask, render_template, request, redirect, url_for, flash
import structlog

from rectifier.config import ConfigReader, ConfigReadError
from rectifier.infrastructure_provider import Heroku
from rectifier.message_brokers import RabbitMQ
from rectifier.rectifier import Rectifier
from rectifier.storage.redis_storage import RedisStorage
from rectifier import settings

from schemas import Config

LOGGER = structlog.get_logger(__name__)

app = Flask(__name__)
storage = RedisStorage()
config_reader = ConfigReader(storage=storage)


class TaskThread(threading.Thread):
    def run(self):
        rectifier = Rectifier(
            storage=RedisStorage(), broker=RabbitMQ(), infrastructure_provider=Heroku()
        )
        while True:
            rectifier.rectify()
            time.sleep(1)


@app.route("/")
def main():
    return render_template(
        'index.html',
        schema=Config.SCHEMA,
        config=json.dumps(config_reader.raw_config, indent=4),
    )


@app.route('/handle_data', methods=['POST'])
def submit_configuration():
    config = request.form['code']
    try:
        ConfigReader.validate(json.loads(config))

        storage.set(settings.REDIS_CONFIG_KEY, config)
        storage.publish(settings.REDIS_CHANNEL, None)

        global config_reader
        config_reader = ConfigReader(storage=storage)

        flash('Succes!', 'info')
    except ConfigReadError as error:
        flash(str(error), 'error')

    return redirect(url_for('main'))


class WebThread(threading.Thread):
    def run(self):
        app.run()


@app.context_processor
def utility_processor():
    def validate_configuration(config):
        if not config:
            return False

        return ConfigReader.is_valid(json.loads(config))

    return dict(validate_configuration=validate_configuration)


t = TaskThread()
t.start()

app.secret_key = '123'
app.run(debug=True)

import threading
import json
import time

from flask import Flask, render_template, request, redirect, url_for, flash
import structlog
from flask_basicauth import BasicAuth

from rectifier.config import ConfigReader, ConfigReadError
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
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)

storage = RedisStorage()
config_reader = ConfigReader(storage=storage)


class TaskThread(threading.Thread):
    def run(self):
        rectifier = Rectifier(
            storage=RedisStorage(), broker=RabbitMQ(), infrastructure_provider=Heroku()
        )
        while True:
            rectifier.run()
            time.sleep(settings.TIME_BETWEEN_REQUESTS)


@app.route("/")
def home():
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

    return redirect(url_for('home'))


class WebThread(threading.Thread):
    def run(self):
        app.run()


t = TaskThread()
t.start()

if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT)

import pytest
import uuid
import sys
import importlib


@pytest.fixture()
def empty_settings():
    settings = importlib.import_module('rectifier.settings')
    yield settings
    del sys.modules['rectifier.settings']


@pytest.fixture()
def heroku_api_key(monkeypatch):
    key = str(uuid.uuid4())
    monkeypatch.setenv('HEROKU_API_KEY', key)

    settings = importlib.import_module('rectifier.settings')
    yield key, settings
    del sys.modules['rectifier.settings']


@pytest.fixture()
def heroku_api_keys(monkeypatch):
    keys = [str(uuid.uuid4()) for _ in range(0, 3)]
    monkeypatch.setenv('HEROKU_API_KEYS', ','.join(keys))

    settings = importlib.import_module('rectifier.settings')
    yield keys, settings
    del sys.modules['rectifier.settings']


def test_empty_config(empty_settings):
    assert empty_settings.HEROKU_API_KEYS == []
    assert empty_settings.HEROKU_API_KEY is None


def test_api_key_set(heroku_api_key):
    (heroku_api_key, settings) = heroku_api_key
    assert settings.HEROKU_API_KEY == heroku_api_key
    assert settings.HEROKU_API_KEYS == [heroku_api_key]


def test_api_keys_set(heroku_api_keys):
    (heroku_api_keys, settings) = heroku_api_keys
    assert settings.HEROKU_API_KEYS == heroku_api_keys

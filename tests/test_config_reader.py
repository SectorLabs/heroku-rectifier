import pytest

from rectifier.config import (
    Config,
    ConfigParser,
    ConfigReadError,
    CoordinatorConfig,
    QueueConfig,
)
from rectifier.config.config import AppConfig
from tests.redis_mock import RedisStorageMock


def test_config_reader_dict_parsing():
    config = {
        'rectifier': {
            'q1': {
                'intervals': [0, 10, 20, 30],
                'workers': [1, 5, 50, 500],
                'cooldown': 30,
                'consumers_formation_name': 'q1w',
            },
            'q2': {
                'intervals': [0, 10, 20, 40],
                'workers': [1, 5, 50, 101],
                'cooldown': 35,
                'consumers_formation_name': 'q2w',
            },
        },
        'rectifier2': {
            'q3': {
                'intervals': [0, 10, 11, 12],
                'workers': [1, 5, 6, 7],
                'cooldown': 12,
                'consumers_formation_name': 'q3w',
            }
        },
    }
    expected_result = Config(
        coordinator_config=CoordinatorConfig(
            apps=dict(
                rectifier=AppConfig(
                    queues=dict(
                        q1=QueueConfig(
                            intervals=[0, 10, 20, 30],
                            workers=[1, 5, 50, 500],
                            cooldown=30,
                            queue_name='q1',
                            consumers_formation_name='q1w',
                        ),
                        q2=QueueConfig(
                            intervals=[0, 10, 20, 40],
                            workers=[1, 5, 50, 101],
                            cooldown=35,
                            queue_name='q2',
                            consumers_formation_name='q2w',
                        ),
                    )
                ),
                rectifier2=AppConfig(
                    queues=dict(
                        q3=QueueConfig(
                            intervals=[0, 10, 11, 12],
                            workers=[1, 5, 6, 7],
                            cooldown=12,
                            queue_name='q3',
                            consumers_formation_name='q3w',
                        )
                    )
                ),
            )
        )
    )

    assert ConfigParser.from_dict(config) == expected_result


def test_config_reader():
    storage = RedisStorageMock()

    config_reader = ConfigParser(storage=storage)
    expected_result = Config(
        coordinator_config=CoordinatorConfig(
            apps=dict(
                rectifier=AppConfig(
                    queues=dict(
                        q1=QueueConfig(
                            intervals=[0, 10, 20, 30],
                            workers=[1, 5, 50, 51],
                            cooldown=30,
                            queue_name='q1',
                            consumers_formation_name='worker_rectifier',
                        )
                    )
                ),
                rectifier2=AppConfig(
                    queues=dict(
                        q21=QueueConfig(
                            intervals=[0, 10, 22, 85],
                            workers=[1, 5, 6, 7],
                            cooldown=120,
                            queue_name='q21',
                            consumers_formation_name='worker_rectifier2',
                        )
                    )
                ),
            )
        )
    )

    assert config_reader.config == expected_result

    storage.set('config', None)
    config_reader = ConfigParser(storage=storage)
    assert config_reader.config is None


@pytest.mark.parametrize(
    'config',
    [
        (
            {
                'rectifier': {
                    'q1': {
                        # Length of intervals and workers don't match
                        'intervals': [0, 10, 20, 30],
                        'workers': [1, 5, 50],
                        'cooldown': 30,
                        'consumers_formation_name': 'q1w',
                    }
                }
            }
        ),
        (
            {
                'rectifier': {
                    'q1': {
                        # Intervals don't start with 0
                        'intervals': [1, 10, 20, 30],
                        'workers': [1, 5, 50, 500],
                        'cooldown': 30,
                        'consumers_formation_name': 'q1w',
                    }
                }
            }
        ),
        (
            {
                'rectifier': {
                    'q1': {
                        'intervals': [0, 1, 20, 30],
                        # Negative workers
                        'workers': [-1, 5, 50, 500],
                        'cooldown': 5,
                        'consumers_formation_name': 'q1w',
                    }
                }
            }
        ),
        (
            {
                'rectifier': {
                    'q1': {
                        'intervals': [0, 1, 20, 30],
                        'workers': [1, 5, 50, 500],
                        # Negative cooldown
                        'cooldown': -1,
                        'consumers_formation_name': 'q1w',
                    }
                }
            }
        ),
        (
            {
                'rectifier': {
                    'q1': {
                        # Not sorted intervals
                        'intervals': [0, 20, 1, 30],
                        'workers': [1, 5, 10, 500],
                        'cooldown': 1,
                        'consumers_formation_name': 'q1w',
                    }
                }
            }
        ),
    ],
)
def test_invalid_queue_configurations(config):
    with pytest.raises(ConfigReadError):
        ConfigParser.validate(config)

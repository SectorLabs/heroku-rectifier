import pytest

from rectifier.config import Config, RabbitMQConfig, BalancerConfig, QueueConfig, ConfigReader, ConfigReadError


def test_config_reader():
    config = {
        'rabbitMQ': {
            'host': 'localhost',
            'port': 80,
            'user': 'admin',
            'password': 'armin',
            'secure': True,
            'vhost': 'vhost'
        },
        'queues': {
            'q1': {
                'intervals': [0, 10, 20, 30],
                'workers': [1, 5, 50, 500],
                'cooldown': 30
            },
            'q2': {
                'intervals': [0, 10, 20, 40],
                'workers': [1, 5, 50, 101],
                'cooldown': 35
            }
        }
    }
    expected_result = Config(
        rabbitMQ_config=RabbitMQConfig(
            host='localhost',
            port=80,
            user='admin',
            password='armin',
            secure=True,
            vhost='vhost'),
        balancer_config=BalancerConfig(
            queues=dict(
                q1=QueueConfig(
                    intervals=[0, 10, 20, 30],
                    workers=[1, 5, 50, 500],
                    cooldown=30,
                    queue_name='q1'),
                q2=QueueConfig(
                    intervals=[0, 10, 20, 40],
                    workers=[1, 5, 50, 101],
                    cooldown=35,
                    queue_name='q2'))))
    assert ConfigReader.from_dict(config) == expected_result


@pytest.mark.parametrize(
    'config',
    [
        ({
            'q1': {
                # Length of intervals and workers don't match
                'intervals': [0, 10, 20, 30],
                'workers': [1, 5, 50],
                'cooldown': 30
            },
        }),
        ({
            'q1': {
                # Intervals don't start with 0
                'intervals': [1, 10, 20, 30],
                'workers': [1, 5, 50, 500],
                'cooldown': 30
            },
        }),
        ({
            'q1': {
                'intervals': [0, 1, 20, 30],
                # Negative workers
                'workers': [-1, 5, 50, 500],
                'cooldown': 5
            },
        }),
        ({
            'q1': {
                'intervals': [0, 1, 20, 30],
                'workers': [1, 5, 50, 500],
                # Negative cooldown
                'cooldown': -1
            },
        }),
        ({
            'q1': {
                # Not sorted intervals
                'intervals': [0, 20, 1, 30],
                'workers': [1, 5, 10, 500],
                'cooldown': 1
            },
        }),
    ])
def test_invalid_queue_configurations(config):
    with pytest.raises(ConfigReadError):
        ConfigReader.balancer_config_from_dict(config)

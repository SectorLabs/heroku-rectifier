import pytest
from uuid import uuid4
from heroku3.api import ResponseError, RateLimitExceeded

from rectifier.infrastructure_provider import Heroku, InfrastructureProviderError
from unittest import mock
from requests import HTTPError


@pytest.mark.parametrize(
    'side_effect',
    [HTTPError(), ResponseError(), RateLimitExceeded()],
)
@mock.patch.object(Heroku, '_key', return_value=str(uuid4()))
def test_scale_errors(_key, side_effect):
    with mock.patch('heroku3.from_key', side_effect=side_effect):
        with pytest.raises(InfrastructureProviderError):
            Heroku().scale('rectifier', {})


@pytest.mark.parametrize('side_effect', [HTTPError(), RateLimitExceeded()])
@mock.patch.object(Heroku, '_key', return_value=str(uuid4()))
def test_broker_uri_errors(_key, side_effect):
    with mock.patch('heroku3.from_key', side_effect=side_effect):
        with pytest.raises(InfrastructureProviderError):
            Heroku().broker_uri('rectifier')

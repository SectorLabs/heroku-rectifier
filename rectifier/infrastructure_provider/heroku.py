from typing import Dict, Tuple
import re

import structlog
import heroku3
from heroku3.api import ResponseError, RateLimitExceeded

from heroku3.models.app import App as HerokuApp
from requests import HTTPError

from rectifier.infrastructure_provider import (
    InfrastructureProvider,
    InfrastructureProviderError,
)
from rectifier import settings
from rectifier.get_random_key import get_random_key
from rectifier.obfuscate_string import obfuscate_string

LOGGER = structlog.get_logger(__name__)


class Heroku(InfrastructureProvider):
    """A wrapper over the Heroku Platofrm API, providing the capability to scale dynos for given queue names."""

    def scale(self, app_name: str, scale_requests: Dict[str, int]) -> None:
        """
        Scales dynos.

        :param app_name: The app for which the batch scale request should be made
        :param scale_requests: What consumers to scale
        """

        LOGGER.info(f"[{app_name}] Scaling: {scale_requests}")

        if settings.DRY_RUN:
            LOGGER.debug('Not pursuing scaling since this is a dry run')
            return

        try:
            app, key = self._connection(app_name)
            app.batch_scale_formation_processes(scale_requests)
        except (HTTPError, ResponseError) as e:
            message = 'Failed to scale.'
            LOGGER.error(message, app=app_name, error=e, key=obfuscate_string(key))
            raise InfrastructureProviderError(message)
        except RateLimitExceeded as e:
            message = 'Rate limit exceeded.'
            LOGGER.error(message, app=app_name, error=e, key=obfuscate_string(key))
            raise InfrastructureProviderError(message)

    def broker_uri(self, app_name: str):
        """
        Retrieves the broker URI for a given app_name
        """

        try:
            app, key = self._connection(app_name)
            return app.config()[settings.BROKER_URL_KEY]
        except HTTPError as e:
            message = 'Cannot retrieve the broker uri.'
            LOGGER.error(message, app=app_name, error=e, key=obfuscate_string(key))
            raise InfrastructureProviderError(message)
        except RateLimitExceeded as e:
            message = 'Rate limit exceeded.'
            LOGGER.error(message, app=app_name, error=e, key=obfuscate_string(key))
            raise InfrastructureProviderError(message)

    @staticmethod
    def _connection(app_name: str) -> Tuple[HerokuApp, str]:
        """Gets a connection to Heroku."""
        key = get_random_key(settings.HEROKU_API_KEYS)

        if not key:
            message = 'No API key set'
            LOGGER.error('No API key set')
            raise InfrastructureProviderError(message)

        conn = heroku3.from_key(key)
        apps = conn.apps()

        if app_name not in apps:
            message = 'App could not be found on Heroku'
            LOGGER.error(message, app=app_name, apps=apps)
            raise InfrastructureProviderError(message)

        return apps[app_name], key

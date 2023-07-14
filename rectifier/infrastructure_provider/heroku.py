from typing import Dict

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

        message = "Scaling" if not settings.DRY_RUN else "Pretending to scale"
        LOGGER.info(f"[{app_name}] {message}: {scale_requests}")

        if settings.DRY_RUN:
            LOGGER.debug('Not pursuing scaling since this is a dry run')
            return

        key = self._key()

        try:
            app = self._connection(app_name, key)
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

        key = self._key()

        try:
            app = self._connection(app_name, key)
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
    def _key() -> str:
        key = get_random_key(settings.HEROKU_API_KEYS)

        if not key:
            message = 'No API key set'
            LOGGER.error('No API key set')
            raise InfrastructureProviderError(message)

        return key

    @staticmethod
    def _connection(app_name: str, api_key: str) -> HerokuApp:
        """Gets a connection to Heroku."""

        conn = heroku3.from_key(api_key)
        try:
            return conn.app(app_name)
        except HTTPError as e:
            if e.response.status_code in (403, 404):
                message = 'App could not be found on Heroku'
                LOGGER.error(message, app=app_name)
                raise InfrastructureProviderError(message) from e

            raise e

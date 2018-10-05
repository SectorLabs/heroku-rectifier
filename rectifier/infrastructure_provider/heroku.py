import structlog
import heroku3

from heroku3.models.app import App as HerokuApp
from requests import HTTPError

from rectifier.infrastructure_provider import (
    InfrastructureProvider,
    InfrastructureProviderError,
)

from rectifier import settings

LOGGER = structlog.get_logger(__name__)


class Heroku(InfrastructureProvider):
    """A wrapper over the Heroku Platofrm API, providing the capability to scale dynos for given queue names."""

    def scale(self, app_name: str, queue_name: str, consumers_count: int) -> None:
        """
        Scales dynos.

        :param queue_name: The queue for which the dynos should be scaled.
        :param consumers_count: The new number of dynos to be used.
        """

        LOGGER.info(
            "Scaling queue %s of app %s to %d consumers"
            % (queue_name, app_name, consumers_count)
        )

        if settings.DRY_RUN:
            LOGGER.debug('Not pursuing scaling since this is a dry run')
            return

        try:
            app = self._connection(app_name)
            app.scale_formation_process(queue_name, consumers_count)
        except HTTPError:
            message = 'Failed to scale.'
            LOGGER.error(message)
            raise InfrastructureProviderError(message)

    def broker_uri(self, app_name: str):
        """
        Retrieves the broker URI for a given app_name
        """

        try:
            app = self._connection(app_name)
            return app.config()[settings.BROKER_URL_KEY]
        except HTTPError:
            message = 'Cannot retrieve the broker uri.'
            LOGGER.error(message)
            raise InfrastructureProviderError(message)

    @staticmethod
    def _connection(app_name: str) -> HerokuApp:
        """Gets a connection to Heroku."""

        conn = heroku3.from_key(settings.HEROKU_API_KEY)
        apps = conn.apps()

        if app_name not in apps:
            message = 'App could not be found on Heroku'
            LOGGER.error(message, app=app_name, apps=apps)
            raise InfrastructureProviderError(message)

        return apps[app_name]

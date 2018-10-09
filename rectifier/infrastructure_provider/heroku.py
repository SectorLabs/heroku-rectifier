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
    def scale(self, queue_name: str, consumers_count: int) -> None:
        LOGGER.info("Scaling queue %s to %d consumers" % (queue_name, consumers_count))

        try:
            app = self._connection()
            app.scale_formation_process(queue_name, consumers_count)
        except HTTPError:
            message = 'Failed to scale.'
            LOGGER.error(message)
            raise InfrastructureProviderError(message)

    def _connection(self) -> HerokuApp:
        """Gets a connection to Heroku."""

        conn = heroku3.from_key(settings.HEROKU_API_KEY)
        apps = conn.apps()

        if settings.HEROKU_APP_NAME not in apps:
            message = 'App could not be found on Heroku'
            LOGGER.error(message, app=settings.HEROKU_APP_NAME, apps=apps)
            raise InfrastructureProviderError(message)

        return apps[settings.HEROKU_APP_NAME]

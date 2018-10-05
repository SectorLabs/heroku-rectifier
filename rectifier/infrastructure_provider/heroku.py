import structlog

from rectifier.infrastructure_provider import InfrastructureProvider

LOGGER = structlog.get_logger(__name__)


class Heroku(InfrastructureProvider):

    def scale(self, queue_name: str, consumers_count: int) -> None:
        LOGGER.info("Scaling queue %s to %d consumers" % (queue_name, consumers_count))

import os

from rectifier import settings
from healthcheck import HealthCheck
from redis.exceptions import ConnectionError, TimeoutError


class HealthChecker:
    """
    Configures a health checker
    """

    def __init__(self, redis_storage):
        self._redis_store = redis_storage
        self._health_check = HealthCheck(
            failed_status=settings.HEALTH_CHECKER_FAILED_STATUS
        )

        self._health_check.add_section(
            'commit', os.environ.get('HEROKU_SLUG_COMMIT', None)
        )
        self._health_check.add_section(
            'release', {"version": os.environ.get('HEROKU_RELEASE_VERSION', None)}
        )
        self._health_check.add_check(self._redis_available)

    def _redis_available(self):
        try:
            info = self._redis_store.redis.info()
        except ConnectionError:
            return False, "Could not connect to Redis instance"
        except TimeoutError:
            return False, "Redis connection timed out"
        return True, info

    def run(self):
        return self._health_check.run()

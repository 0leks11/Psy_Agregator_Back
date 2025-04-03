from django.db.backends.postgresql import base as postgresql
from django.conf import settings

class DatabaseWrapper(postgresql.DatabaseWrapper):
    def _configure_timezone(self, connection):
        if getattr(settings, 'POSTGRES_DISABLE_TIMEZONE_SET', False):
            return False  # Не устанавливаем часовой пояс
        return super()._configure_timezone(connection) 
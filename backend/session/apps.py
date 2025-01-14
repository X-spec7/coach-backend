import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SessionConfig(AppConfig):
    name = 'backend.session'
    verbose_name = _("Session")

    def ready(self):
        with contextlib.suppress(ImportError):
            import backend.users.signals  # noqa: F401

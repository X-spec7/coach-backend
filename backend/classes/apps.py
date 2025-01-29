import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ClassesConfig(AppConfig):
    name = 'backend.classes'
    verbose_name = _("Class")

    def ready(self):
        with contextlib.suppress(ImportError):
            import backend.classes.signals  # noqa: F401

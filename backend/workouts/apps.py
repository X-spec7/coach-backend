import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkoutsConfig(AppConfig):
    name = 'backend.workouts'
    verbose_name = _("Workouts")

    def ready(self):
        with contextlib.suppress(ImportError):
            import backend.workouts.signals  # noqa: F401
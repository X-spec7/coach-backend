import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExercisesConfig(AppConfig):
    name = 'backend.exercises'
    verbose_name = _("Exercise")

    def ready(self):
        with contextlib.suppress(ImportError):
            import backend.exercises.signals  # noqa: F401

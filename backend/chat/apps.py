import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ChatConfig(AppConfig):
    name = 'backend.chat'
    verbose_name = _("Chat")

    def ready(self):
        with contextlib.suppress(ImportError):
            import backend.users.signals  # noqa: F401
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SessionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.session'
    verbose_name = _("Session App")

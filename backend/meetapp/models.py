from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Session(models.Model):
    session_name = models.CharField(max_length=255, blank=False, null=False)
    category = models.CharField(max_length=255, blank=False, null=False)
    start_time = models.DateTimeField(blank=False, null=False)
    duration = models.IntegerField(blank=False, null=False)
    zoom_id = models.CharField(max_length=255, blank=False, null=False)
    encrypted_password = models.CharField(max_length=255, blank=False, null=False)
    join_url = models.CharField(max_length=255, blank=False, null=False)
    creator = models.ForeignKey(User, related_name =_("session_creator"), blank=False, null=False, on_delete=models.CASCADE)
    booked_users = models.ManyToManyField(User, related_name="booked_sessions", blank=True)

    def __str__(self):
        return f"{self.session_name}"

    class Meta:
        app_label = "meetapp"

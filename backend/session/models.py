from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import models
from backend.users.models import User
from backend.classes.models import Class

class Meeting(models.Model):
    start_time = models.DateTimeField(blank=False, null=False)
    duration = models.IntegerField(blank=False, null=False)
    meeting_number = models.CharField(max_length=255, blank=False, null=False)
    encrypted_password = models.CharField(max_length=255, blank=False, null=False)
    join_url = models.TextField(blank=False, null=False)
    start_url = models.TextField(blank=False, null=False)
    creator = models.ForeignKey(User, related_name=_("session_creator"), blank=False, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.meeting_number}"

    class Meta:
        app_label = "session"


class Session(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    start_date = models.DateTimeField(null=False)
    duration = models.IntegerField(null=False)
    coach = models.ForeignKey(User, verbose_name=_("Session Creator"), related_name="session", on_delete=models.CASCADE)
    goal = models.CharField(max_length=100, blank=False, null=False)
    level = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    banner_image = models.ImageField(
        _("Session Banner Image"),
        upload_to="session_banner_images/",
        null=True,
        blank=True,
    )
    current_participant_number = models.IntegerField(null=False, default=0)
    total_participant_number = models.IntegerField(null=False)
    price = models.IntegerField(null=False)
    equipments = models.JSONField(blank=True, null=True)
    booked_users = models.ManyToManyField(User, verbose_name=_("Booked Users"), related_name="booked_sessions")
    meeting = models.OneToOneField(Meeting, verbose_name=_(""), on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        app_label = "session"
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")

class ClassSession(Session):
    price = None
    goal = None
    level = None
    banner_image = None
    coach = None
    calorie = models.IntegerField(null=False, blank=False)

    used_class = models.ForeignKey(Class, verbose_name=_("Using Class"), related_name="session_class", on_delete=models.CASCADE)
    
    class Meta:
        app_label = "session"
        verbose_name = _("Class Session")
        verbose_name_plural = _("Class Sessions")

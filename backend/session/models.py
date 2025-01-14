from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Session(models.Model):
  title = models.CharField(max_length=255, blank=False, null=False)
  startDate = models.DateTimeField(null=False)
  duration = models.Integer(null=False)
  coach = models.ForeignKey("User", verbose_name=_("Session Creator"), on_delete=models.CASCADE)
  goal = models.CharField(max_length=100, blank=False, null=False)
  level = models.CharField(max_length=100, blank=False, null=False)
  description = models.CharField(max_length=255, blank=False, null=False)
  totalParticipantNumber = models.IntegerField(null=False)
  price = models.IntegerField(null=False)
  equipments = models.ArrayField(base_field=[])
  meeting = models.OneToOneField("app.Model", verbose_name=_(""), on_delete=models.CASCADE)

  def __str__(self):
    return f"{self.session_name}"
  
  class Meta:
    app_label = "session"
    
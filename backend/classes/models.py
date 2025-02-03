from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.users.models import User

class Class(models.Model):
  """Represents a fitness class with assigned exercises."""
  coach = models.ForeignKey(
    User,
    related_name="creator",
    on_delete=models.CASCADE,
    limit_choices_to={"user_type": "Coach"},
    blank=False
  )
  title = models.CharField(_("Title"), max_length=50)
  category = models.CharField(_("Category"), max_length=50)
  description = models.TextField(_("Description"), blank=True, null=True)
  intensity = models.CharField(_("Intensity"), max_length=50)
  level = models.CharField(_("Level"), max_length=50)
  price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
  session_count = models.PositiveIntegerField(_("Session Count"), default=0)
  duration_per_session = models.PositiveIntegerField(_("Duration per Session (minutes)"), null=True, blank=True)
  calorie_per_session = models.PositiveIntegerField(_("Calorie Burn per Session"), null=True, blank=True)

  benefits = models.JSONField(_("Benefits"), default=list, blank=True)
  equipments = models.JSONField(_("Equipments"), default=list, blank=True)
  booked_users = models.ManyToManyField(
    User,
    related_name="booked_classes",
    limit_choices_to={"user_type": "Client"},
    blank=True
  )

  banner_image = models.ImageField(
    _("Session Banner Image"),
    upload_to="session_banner_images/",
    null=True,
    blank=True,
  )

  def __str__(self):
    return f"{self.title} ({self.level} - {self.intensity})"

  class Meta:
    app_label = "classes"
    verbose_name = _("Class")
    verbose_name_plural = _("Classes")

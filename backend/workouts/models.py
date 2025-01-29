from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.users.models import User

class Workout(models.Model):
  """A Basic workout plan"""
  title = models.CharField(_("Title"), max_length=255)
  descriptions = models.CharField(_("Description"), max_length=255)
  created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

  def __str__(self):
    return f"{self.title} - {self.client.full_name}"

  class Meta:
    app_label = "workouts"
    verbose_name = _("Workout")
    verbose_name_plural = _("Workouts")

class ClientWorkout(Workout):
  """A workout plan created by the client."""

  client = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name="client_workouts",
    limit_choices_to={"user_type": "Client"},
  )
  class Meta:
    app_label = "workouts"
    verbose_name = _("Client Workout")
    verbose_name_plural = _("Client Workouts")

# TODO: create class workout

class WorkoutDailyPlan(models.Model):
  """Represents a daily workout plan with exercises."""
  workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="daily_plans")
  date = models.DateField(_("Date"))

  def __str__(self):
    return f"Plan for {self.date} in {self.workout.title}"

  class Meta:
    app_label = "workouts"
    verbose_name = _("Daily Plan")
    verbose_name_plural = _("Daily Plans")

# TODO: create class daily plan

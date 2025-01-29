from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.users.models import User
from backend.classes.models import Class

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

class ClassWorkout(Workout):
  """A workout plan used in a class."""

  used_class = models.ForeignKey(
    Class,
    on_delete=models.CASCADE,
    related_name="class_workouts",
  )

class ClientWorkoutDailyPlan(models.Model):
  """Represents a daily client workout plan with exercises."""
  workout = models.ForeignKey(ClientWorkout, on_delete=models.CASCADE, related_name="client_workout_daily_plans")
  date = models.DateField(_("Date"))

  def __str__(self):
    return f"Plan for {self.date} in {self.workout.title}"

  class Meta:
    app_label = "workouts"
    verbose_name = _("Client Workout Daily Plan")
    verbose_name_plural = _("Client Workout Daily Plans")

class ClassWorkoutDailyPlan(models.Model):
  """Represents a daily class workout plan with exercises."""

  workout = models.ForeignKey(ClassWorkout, on_delete=models.CASCADE, related_name="class_workout_daily_plans")
  date = models.DateField(_("Date"))

  def __str__(self):
    return f"Plan for {self.date} in {self.workout.title}"

  class Meta:
    app_label = "workouts"
    verbose_name = _("Class Workout Daily Plan")
    verbose_name_plural = _("Class Worktout Daily Plans")
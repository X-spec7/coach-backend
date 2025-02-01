from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.workouts.models import ClientWorkoutDailyPlan
from backend.classes.models import Class
class Exercise(models.Model):
  title = models.CharField(_("Title"), max_length=255, unique=True)
  description = models.TextField(_("Description"), blank=True, null=True)
  icon = models.ImageField(_("Exercise Icon"), upload_to="exercise_icons/", blank=True, null=True)
  gif = models.ImageField(_("Exercise GIF"), upload_to="exercise_gifs/", blank=True, null=True)
  calorie_per_round = models.PositiveIntegerField(_("Calorie Burnt per one time"), default=5)
  
  created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
  updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

  def __str__(self):
    return self.title

  class Meta:
    app_label = "exercises"
    verbose_name = _("Exercise")
    verbose_name_plural = _("Exercises")
    ordering = ["title"]

class WorkoutExercise(models.Model):
  """Exercises included in a Client Workout Daily Plan, linked to the main Exercise model."""
  daily_plan = models.ForeignKey(ClientWorkoutDailyPlan, on_delete=models.CASCADE, related_name="workout_exercises")
  exercise = models.ForeignKey("Exercise", on_delete=models.CASCADE, related_name="workout_instances")
  set_count = models.PositiveIntegerField(_("Set Count"), default=3)
  reps_count = models.PositiveIntegerField(_("Reps Count"), default=10)
  rest_duration = models.PositiveIntegerField(_("Rest Duration (seconds)"), default=30)
  calorie = models.PositiveIntegerField(_("Calorie Burnt per Set"), default=50)

  def __str__(self):
    return f"{self.exercise.title} - {self.set_count} Sets x {self.reps_count} Reps"

  class Meta:
    app_label = "exercises"
    verbose_name = _("Workout Exercise")
    verbose_name_plural = _("Workout Exercises")

class ClassExercise(models.Model):
  """Exercises included in a Class Workout Daily Plan, linked to the main Exercise model."""
  class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_exercise")
  exercise = models.ForeignKey("Exercise", on_delete=models.CASCADE, related_name="workout_instances")
  set_count = models.PositiveIntegerField(_("Set Count"), default=3)
  reps_count = models.PositiveIntegerField(_("Reps Count"), default=10)
  rest_duration = models.PositiveIntegerField(_("Rest Duration (seconds)"), default=30)
  calorie_per_set = models.PositiveIntegerField(_("Calorie Burnt per Set"), default=50)

  def __str__(self):
    return f"{self.exercise.title} - {self.set_count} Sets x {self.reps_count} Reps"

  class Meta:
    app_label = "exercises"
    verbose_name = _("Workout Exercise")
    verbose_name_plural = _("Workout Exercises")


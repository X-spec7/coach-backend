from django.db import models
from django.utils.translation import gettext_lazy as _

class Exercise(models.Model):
  title = models.CharField(_("Title"), max_length=255, unique=True)
  description = models.TextField(_("Description"), blank=True, null=True)
  icon = models.ImageField(_("Exercise Icon"), upload_to="exercise_icons/", blank=True, null=True)
  gif = models.ImageField(_("Exercise GIF"), upload_to="exercise_gifs/", blank=True, null=True)
  
  created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
  updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

  def __str__(self):
    return self.title

  class Meta:
    app_label = "exercises"
    verbose_name = _("Exercise")
    verbose_name_plural = _("Exercises")
    ordering = ["title"]

from typing import ClassVar
import uuid
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField
from django.utils.timezone import now
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    full_name = CharField(_("Full Name"), max_length=50, default="John Doe")
    first_name = CharField(_("First Name"), max_length=50, default="John")
    last_name = CharField(_("Last Name"), max_length=50, default="Doe")
    user_type = CharField(_("User Type"), max_length=50, default="Client")
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    address = models.CharField(_("Address"), max_length=20, blank=True)
    email = EmailField(_("Email Address"), unique=True)
    username = None
    avatar_image = models.ImageField(
        _("User Image"),
        upload_to="user_images/",
        null=True,
        blank=True,
    )
    email_verified = models.BooleanField(_("Email Verified"), default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def is_coach(self):
        return self.user_type == "Coach"

    def is_client(self):
        return self.user_type == "Client"

    def get_absolute_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.id})
    
    def qualifications_list(self):
        return ", ".join([f"{q.name} ({q.year})" for q in self.qualifications.all()])

    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

class CoachReview(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_coach", limit_choices_to={"user_type": "Coach"})
    reviewer_name = CharField(_("Reviewer Full Name"), max_length=50, null=False, blank=False)
    reviewer_avatar = models.ImageField(
        _("Review Avatar Image"),
        upload_to="user_images/",
        null=True,
        blank=True,
    )
    rating = models.PositiveIntegerField(_("Review Rating"), blank=False, null=False)
    content = models.TextField(_("review_content"))


class CoachProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="coach_profile", limit_choices_to={"user_type": "Coach"})
    certification = models.CharField(_("Certification"), max_length=255, blank=True, null=True)
    specialization = models.CharField(_("Specialization"), max_length=255, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(_("Years of Experience"), blank=True, null=True)

    # TODO: apply this after creating classes table
    # classes = models.ManyToManyField("Class", related_name="coaches", blank=True)
    # sessions = models.ManyToManyField(Session, related_name="coaches", blank=True)
    banner_image = models.ImageField(
        _("Banner Image"),
        upload_to="banner_images/",
        null=True,
        blank=True,
    )
    # TODO!: update default value to false after admin feature is ready
    listed = models.BooleanField(_("Listed"), default=True, help_text=_("Indicates whether the coach is approved by the admin"))

class Certification(models.Model):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    certification_title = models.CharField(_("Certification Title"), max_length=255)
    certification_detail = models.CharField(_("Certification Detail"), max_length=255)

    def __str__(self):
        return f"{self.certification_title} ({self.certification_detail})"

    class Meta:
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")


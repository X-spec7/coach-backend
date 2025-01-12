from typing import ClassVar
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import CharField, EmailField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class EncryptedUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)

class Qualification(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Qualification Name"))
    year = models.PositiveIntegerField(verbose_name=_("Year Obtained"))

    def __str__(self):
        return f"{self.name} ({self.year})"  
    
    class Meta:
        app_label = 'users'


class User(AbstractUser):

    USER_TYPE_CHOICES = [
        ("User", _("Coach")),
        ("Client", _("Client")),
    ]

    full_name = CharField(_("Full Name"), max_length=255, default="John Doe")
    first_name = CharField(_("First Name"), max_length=255, default="John")
    last_name = CharField(_("Last Name"), max_length=255, default="Doe")
    user_type = CharField(_("User Type"), max_length=50, choices=USER_TYPE_CHOICES, default="Client")
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    address = models.CharField(_("Phone Number"), max_length=20, blank=True)
    email = EmailField(_("Email Address"), unique=True)
    username = None
    avatar_image = models.ImageField(
        _("User Image"),
        upload_to="user_images/",
        null=True,
        blank=True,
    )
    banner_image = models.ImageField(
        _("Banner Image"),
        upload_to="banner_images/",
        null=True,
        blank=True,
    )
    email_verified = models.BooleanField(_("Email Verified"), default=False)
    years_of_experience = models.PositiveIntegerField(
        _("Years of Experience"), null=True, blank=True
    )
    specialization = models.CharField(
        _("Specialization"), max_length=255, blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.id})
    
    def qualifications_list(self):
        return ", ".join([f"{q.name} ({q.year})" for q in self.qualifications.all()])

    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

class UserQualification(models.Model):
    user = models.ForeignKey(User, related_name='qualifications', on_delete=models.CASCADE)
    qualification = models.ForeignKey(Qualification, related_name='users', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'qualification')
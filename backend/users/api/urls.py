from django.urls import path
from .views import (
  LoginView,
  RegisterView,
  MailVerifyView,
)

urlpatterns = [
    path("login/", view=LoginView.as_view(), name="login"),
    path("register/", view=RegisterView.as_view(), name="register"),
    path("mail-verify/", view=MailVerifyView.as_view(), name="mailverify"),
]

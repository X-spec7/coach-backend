from django.urls import path
from .views import (
  LoginView,
  RegisterView,
  GetUserProfileView,
  MailVerifyView,
  UpdateProfileView
)

urlpatterns = [
    path("login/", view=LoginView.as_view(), name="login"),
    path("register/", view=RegisterView.as_view(), name="register"),
    path("profile/update/", view=UpdateProfileView.as_view(), name="updateProfile"),
    path("mail-verify/", view=MailVerifyView.as_view(), name="mailverify"),
    path("profile/get/", view=GetUserProfileView.as_view(), name="getUserInfo"),
]

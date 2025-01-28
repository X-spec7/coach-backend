from django.urls import path
from .views import GetUserProfileView, UpdateUserProfileView

app_name = "users"
urlpatterns = [
  path("profile/get/", view=GetUserProfileView.as_view(), name="get_user_profile"),
  path("profile/update/", view=UpdateUserProfileView.as_view(), name="update_user_profile")
]

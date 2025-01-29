from django.urls import path
from .views import GetUserProfileView, UpdateClientProfileView, UpdateCoachProfileView

app_name = "users"
urlpatterns = [
  path("profile/get/", view=GetUserProfileView.as_view(), name="get_user_profile"),
  path("profile/client/update/", view=UpdateClientProfileView.as_view(), name="update_client_profile"),
  path("profile/coach/update/", view=UpdateCoachProfileView.as_view(), name="update_user_profile")
]

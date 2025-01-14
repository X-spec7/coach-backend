from django.urls import path
from .views import CreateSessionView, GetSessionsView, CreateMeetingView

urlpatterns = [
  path("create/", view=CreateSessionView.as_view(), name="create session"),
  path("get/", view=GetSessionsView.as_view(), name="get sessions"),
  path("create/meeting/", view=CreateMeetingView.as_view(), name="create sessions"),
]

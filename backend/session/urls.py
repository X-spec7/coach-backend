from django.urls import path
from .views import (
  CreateSessionView,
  GetSessionsView,
  CreateMeetingView,
  BookSessionView
)

urlpatterns = [
  path("create/", view=CreateSessionView.as_view(), name="create session"),
  path("get/", view=GetSessionsView.as_view(), name="get sessions"),
  path("create/meeting/", view=CreateMeetingView.as_view(), name="create sessions"),
  path("book/", view=BookSessionView.as_view(), name="book session"),
]

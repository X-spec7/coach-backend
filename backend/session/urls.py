from django.urls import path
from .views import (
  CreateSessionView,
  GetSessionsView,
  GetSessionTotalCountView,
  GetMySessionsView,
  GetMySessionTotalCountView,
  CreateMeetingView,
  BookSessionView,
  JoinSessionView,
)

urlpatterns = [
  path("create/", view=CreateSessionView.as_view(), name="create session"),
  path("join/", view=JoinSessionView.as_view(), name="join session"),
  path("get/", view=GetSessionsView.as_view(), name="get sessions"),
  path("get/count/", view=GetSessionTotalCountView.as_view(), name="get session count"),
  path("get/mine/", view=GetMySessionsView.as_view(), name="get sessions"),
  path("get/mine/count/", view=GetMySessionTotalCountView.as_view(), name="get session count"),
  path("book/", view=BookSessionView.as_view(), name="book session"),
  path("create/instant/", view=CreateMeetingView.as_view(), name="create sessions"),
]

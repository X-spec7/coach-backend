from django.urls import path
from .views import (
  CreateClassView,
  GetClassesView,
  GetClassByIdView,
  BookClassView,
  StartClassSessionView,
  JoinClassSessionView,
)

app_name="classes"

urlpatterns = [
  path("create/", view=CreateClassView.as_view(), name="create_class"),
  path("get/", view=GetClassesView.as_view(), name="get_classes"),
  path("get/<int:class_id>/", view=GetClassByIdView.as_view(), name="get_class_by_id"),
  path("book/<int:class_id>/", view=BookClassView.as_view(), name="book_class"),
  path("session/start/<int:class_session_id>/", view=StartClassSessionView.as_view(), name="start_class_session"),
  path("session/join/<int:class_session_id>/", view=JoinClassSessionView.as_view(), name="join_class_session"),
]

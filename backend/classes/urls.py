from django.urls import path
from .views import (
  CreateClassView,
  GetClassesView,
)

app_name="classes"

urlpatterns = [
  path("create/", view=CreateClassView.as_view(), name="create_class_view"),
  path("get/", view=GetClassesView.as_view(), name="get_classes_view"),
]

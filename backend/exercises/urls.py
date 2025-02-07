from django.urls import path
from .views import (
  CreateExerciseView
)

urlpatterns = [
  path('create/', view=CreateExerciseView.as_view(), name="create_exercise")
]

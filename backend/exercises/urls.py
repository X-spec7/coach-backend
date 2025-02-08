from django.urls import path
from .views import (
  CreateExerciseView,
  GetExercisesView,
  UpdateExerciseView,
)

urlpatterns = [
  path('create/', view=CreateExerciseView.as_view(), name="create_exercise"),
  path('get/', view=GetExercisesView.as_view(), name="get_exercises"),
  path('update/', view=UpdateExerciseView.as_view(), name="update_exercises"),
]

from rest_framework import serializers
from backend.classes.models import Class

from django.conf import settings

class GetClassesRequestDTO(serializers.Serializer):
  limit = serializers.IntegerField(min_value=1, required=True)
  offset = serializers.IntegerField(min_value=0, required=True)
  query = serializers.CharField(max_length=50, required=False, allow_null=True)
  category = serializers.CharField(max_length=50, required=False, allow_null=True)
  level = serializers.CharField(max_length=50, required=False, allow_null=True)

class ClassSerializer(serializers.ModelSerializer):
  coachId = serializers.IntegerField(source='id')
  caloriePerSession = serializers.IntegerField(source='calorie_per_session')
  sessionCount = serializers.IntegerField(source='session_count')
  durationPerSession = serializers.IntegerField(source='duration_per_session')

  coachFullname = serializers.SerializerMethodField()
  classBannerImageUrl = serializers.SerializerMethodField()
  exercises = serializers.SerializerMethodField()

  class Meta:
    model = Class
    fields = [
      "id", "title", "description", "category", "intensity", "level", "price", "benefits", "equipments"
      "coachId", "classBannerImageUrl", "coachFullname", "sessionCount", "durationPerSession", "caloriePerSession", "exercises"
    ]

  def get_coachFullname(self, obj):
    return obj.coach.full_name if obj.coach else None

  def get_classBannerImageUrl(self, obj):
    if obj.banner_image:
      return f"{settings.MEDIA_URL}{obj.banner_image}"
  
  def get_exercises(self, obj):
    class_exercises = obj.class_exercises.all()

    formatted_exercises = [
      {
        "id": class_exercise.id,
        "title": class_exercise.exercise.title,
        "description": class_exercise.exercise.description,
        "exerciseIconUrl": f"{settings.MEDIA_URL}{class_exercise.exercise.icon}" if class_exercise.icon else None,
        "exerciseGifUrl": f"{settings.MEDIA_URL}{class_exercise.exercise.gif}" if class_exercise.gif else None,
        "caloriePerRound": class_exercise.exercise.calorie_per_round,
        "setCount": class_exercise.set_count,
        "repsCount": class_exercise.reps_count,
        "restDuration": class_exercise.rest_duration,
        "caloriePerSet": class_exercise.calorie_per_set
      }
      for class_exercise in class_exercises
    ]

    return formatted_exercises

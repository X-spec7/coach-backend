import re
from rest_framework import serializers
from backend.classes.models import Class

from django.conf import settings

def camel_to_snake(name):
  """Convert camelCase to snake_case."""
  return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

class GetClassesRequestDTO(serializers.Serializer):
  limit = serializers.IntegerField(min_value=1, default=6)
  offset = serializers.IntegerField(min_value=0, default=0)
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

class ClassExerciseSerializer(serializers.Serializer):
  id = serializers.IntegerField()
  title = serializers.CharField()
  description = serializers.CharField()
  exercise_icon_url = serializers.CharField()
  exercise_gif_url = serializers.CharField()
  calorie_per_round = serializers.FloatField()
  set_count = serializers.IntegerField()
  reps_count = serializers.IntegerField()
  rest_duration = serializers.IntegerField()
  calorie_per_set = serializers.FloatField()

  def to_internal_value(self, data):
    """Convert camelCase request fields to snake_case before validation."""
    converted_data = {camel_to_snake(k): v for k, v in data.items()}
    return super().to_internal_value(converted_data)

  def to_representation(self, instance):
    """Convert snake_case fields to camelCase when returning data."""
    data = super().to_representation(instance)
    return {re.sub(r'_([a-z])', lambda x: x.group(1).upper(), k): v for k, v in data.items()}

class ClassSessionSerializer(serializers.Serializer):
  title = serializers.CharField()
  start_date = serializers.DateTimeField()
  duration = serializers.IntegerField()
  description = serializers.CharField()
  total_participant_number = serializers.IntegerField()
  calorie = serializers.FloatField()
  equipments = serializers.ListField(child=serializers.CharField(), required=False)

  def to_internal_value(self, data):
    """Convert camelCase request fields to snake_case before validation."""
    converted_data = {camel_to_snake(k): v for k, v in data.items()}
    return super().to_internal_value(converted_data)

  def to_representation(self, instance):
    """Convert snake_case fields to camelCase when returning data."""
    data = super().to_representation(instance)
    return {re.sub(r'_([a-z])', lambda x: x.group(1).upper(), k): v for k, v in data.items()}

class CreateClassRequestSerializer(serializers.Serializer):
  title = serializers.CharField(max_length=50)
  category = serializers.CharField(max_length=100)
  description = serializers.CharField()
  intensity = serializers.CharField(max_length=50)
  level = serializers.CharField(max_length=50)
  price = serializers.FloatField()
  session_count = serializers.IntegerField(min_value=1)
  duration_per_session = serializers.IntegerField(min_value=1)
  calorie_per_session = serializers.IntegerField(min_value=0)
  benefits = serializers.ListField(child=serializers.CharField())
  equipments = serializers.ListField(child=serializers.CharField(), required=False)
  banner_image = serializers.CharField(allow_null=True, required=False)
  exercises = ClassExerciseSerializer(many=True)
  sessions = ClassSessionSerializer(many=True)

  def to_internal_value(self, data):
    """Convert camelCase request fields to snake_case before validation."""
    converted_data = {camel_to_snake(k): v for k, v in data.items()}
    return super().to_internal_value(converted_data)

  def to_representation(self, instance):
    """Convert snake_case fields to camelCase when returning data."""
    data = super().to_representation(instance)
    return {re.sub(r'_([a-z])', lambda x: x.group(1).upper(), k): v for k, v in data.items()}

  def validate_banner_image(self, value):
    """Ensure banner image is a valid base64-encoded string if provided."""
    if value and not value.startswith('data:image/'):
      raise serializers.ValidationError("Invalid image format.")
    return value

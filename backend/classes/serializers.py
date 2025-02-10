import re
from rest_framework import serializers
from backend.classes.models import Class
from backend.exercises.models import ClassExercise
from backend.session.models import ClassSession

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
  caloriePerSession = serializers.IntegerField(source='calorie_per_session')
  sessionCount = serializers.IntegerField(source='session_count')
  durationPerSession = serializers.IntegerField(source='duration_per_session')

  coachId = serializers.SerializerMethodField()
  coachFullname = serializers.SerializerMethodField()
  classBannerImageUrl = serializers.SerializerMethodField()
  exercises = serializers.SerializerMethodField()
  sessions = serializers.SerializerMethodField()
  booked = serializers.SerializerMethodField()

  class Meta:
    model = Class
    fields = [
      "id", "title", "description", "category", "intensity", "level", "price", "benefits", "equipments",
      "coachId", "classBannerImageUrl", "coachFullname", "sessionCount", "durationPerSession", "caloriePerSession", "exercises", "sessions", "booked",
    ]

  def get_coachId(self, obj):
    return obj.coach.id if obj.coach else None

  def get_coachFullname(self, obj):
    return obj.coach.full_name if obj.coach else None

  def get_classBannerImageUrl(self, obj):
    if obj.banner_image:
      return f"{settings.MEDIA_URL}{obj.banner_image}"
    
  def get_booked(self, obj):
    """Checks if the current user has booked this class."""
    request = self.context.get("request")
    if request and request.user.is_authenticated:
        return obj.booked_users.filter(id=request.user.id).exists()
    return False
  
  def get_exercises(self, obj):
    class_exercises = ClassExercise.objects.filter(class_ref=obj)

    formatted_exercises = [
      {
        "id": class_exercise.id,
        "title": class_exercise.exercise_ref.title,
        "description": class_exercise.exercise_ref.description,
        "exerciseIconUrl": f"{settings.MEDIA_URL}{class_exercise.exercise_ref.icon}" if class_exercise.exercise_ref.icon else None,
        "exerciseGifUrl": f"{settings.MEDIA_URL}{class_exercise.exercise_ref.gif}" if class_exercise.exercise_ref.gif else None,
        "caloriePerRound": class_exercise.exercise_ref.calorie_per_round,
        "setCount": class_exercise.set_count,
        "repsCount": class_exercise.reps_count,
        "restDuration": class_exercise.rest_duration,
        "caloriePerSet": class_exercise.calorie_per_set
      }
      for class_exercise in class_exercises
    ]

    return formatted_exercises
  
  def get_sessions(self, obj):
    class_sessions = ClassSession.objects.filter(class_ref=obj)

    formatted_sessions = [
      {
        "id": class_session.id,
        "title": class_session.title,
        "startDate": class_session.start_date,
        "duration": class_session.duration,
        "description": class_session.description,
        "totalParticipantNumber": class_session.total_participant_number,
        "calorie": class_session.calorie,
        "equipments": class_session.equipments,
      }
      for class_session in class_sessions
    ]

    return formatted_sessions

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

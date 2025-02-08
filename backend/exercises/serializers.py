from rest_framework import serializers

from backend.exercises.models import Exercise

from django.conf import settings

class ExerciseSerializer(serializers.ModelSerializer):
  caloriePerRound = serializers.IntegerField(source="calorie_per_round")
  exerciseIconUrl = serializers.SerializerMethodField()
  exerciseGifUrl = serializers.SerializerMethodField()

  class Meta:
    model = Exercise
    fields = [
      'id',
      'title',
      'description',
      'caloriePerRound',
      'exerciseIconUrl',
      'exerciseGifUrl',
    ]

  def get_exerciseIconUrl(self, obj):
    if obj.icon:
      return f"{settings.MEDIA_URL}{obj.icon}"
    return None
  
  def get_exerciseGifUrl(self, obj):
    if obj.gif:
      return f"{settings.MEDIA_URL}{obj.gif}"
    return None
  
class CreateExerciseRequestDTO(serializers.Serializer):
  title = serializers.CharField(required=True)
  description = serializers.CharField(required=True)
  caloriePerRound = serializers.IntegerField(required=True)
  exerciseIcon = serializers.CharField(required=False, allow_blank=True)
  exerciseGif = serializers.CharField(required=False, allow_blank=True)

class UpdateExerciseRequestDTO(CreateExerciseRequestDTO):
  exerciseId = serializers.IntegerField(required=True)

class GetExerciseRequestDTO(serializers.Serializer):
  query = serializers.CharField(required=False, allow_blank=True)
  limit = serializers.IntegerField(required=False, default=15)
  offset = serializers.IntegerField(required=False, default=0)
  
from rest_framework import serializers

from backend.session.models import Session

from django.conf import settings

class SessionSerializer(serializers.ModelSerializer):
  bannerImageUrl = serializers.SerializerMethodField()
  coachId = serializers.SerializerMethodField()
  coachFullname = serializers.SerializerMethodField()
  meetingId = serializers.SerializerMethodField()

  startDate = serializers.DateTimeField(source="start_date")
  totalParticipantNumber = serializers.IntegerField(source="total_participant_number")
  currentParticipantNumber = serializers.IntegerField(source="current_participant_number")

  class Meta:
    model = Session
    fields = [
      'id',
      'title',
      'startDate',
      'duration',
      'coachId',
      'coachFullname',
      'goal',
      'level',
      'description',
      'totalParticipantNumber',
      'bannerImageUrl',
      'totalParticipantNumber',
      'currentParticipantNumber',
      'price',
      'equipments',
      'meetingId',
    ]

  def get_bannerImageUrl(self, obj):
    if obj.banner_image:
      return f"{settings.MEDIA_URL}{obj.banner_image}"
    return None

  def get_coachId(self, obj):
    return obj.coach.id if obj.coach else None

  def get_coachFullname(self, obj):
    if obj.coach:
      return f"{obj.coach.first_name} {obj.coach.last_name}"
    return None

  def get_meetingId(self, obj):
    return obj.meeting.id if obj.meeting else None
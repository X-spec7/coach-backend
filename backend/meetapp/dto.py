from rest_framework import serializers

class CreateSessionRequestDTO(serializers.Serializer):
    topic = serializers.CharField(max_length=255, required=True, allow_blank=False)
    agenda = serializers.CharField(max_length=255, required=True, allow_blank=False)
    category = serializers.CharField(max_length=255, required=True, allow_blank=False)
    start_time = serializers.DateTimeField(required=True)
    duration = serializers.IntegerField(required=True)

class CreateInstantMeetingRequestDTO(serializers.Serializer):
    recipient_id = serializers.CharField(max_length=255, required=True, allow_blank=False)

class MeetingAuthorizationRequestDTO(serializers.Serializer):
    meeting_number = serializers.CharField(max_length=255, required=True, allow_blank=False)
    role = serializers.IntegerField(required=True)
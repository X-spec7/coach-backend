from rest_framework import serializers

class GetSessionsRequestDTO(serializers.Serializer):
  limit = serializers.IntegerField(min_value=1, required=True)
  offset = serializers.IntegerField(min_value=0, required=True)
  goal = serializers.CharField(max_length=255, required=False, allow_null=True)
  booked = serializers.BooleanField(required=False)
  query = serializers.CharField(max_length=255, required=False, allow_null=True)

class GetTotalSessionCountRequestDTO(serializers.Serializer):
  goal = serializers.CharField(max_length=255, required=False, allow_null=True)
  booked = serializers.BooleanField(required=False)
  query = serializers.CharField(max_length=255, required=False, allow_null=True)

class GetMySessionTotalCountRequestDTO(serializers.Serializer):
  query = serializers.CharField(max_length=255, required=False, allow_null=True)

class GetMySessionsRequestDTO(serializers.Serializer):
  limit = serializers.IntegerField(min_value=1, required=True)
  offset = serializers.IntegerField(min_value=0, required=True)
  query = serializers.CharField(max_length=255, required=False, allow_null=True)

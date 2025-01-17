from rest_framework import serializers

class GetUsersListDTO(serializers.Serializer):
  limit = serializers.IntegerField(min_value=1, required=True)
  offset = serializers.IntegerField(min_value=0, required=True)
  query = serializers.CharField(max_length=255, required=False, allow_null=True)
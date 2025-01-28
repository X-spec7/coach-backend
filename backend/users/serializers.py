from rest_framework import serializers

from backend.users.models import User

from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    avatarImageUrl = serializers.SerializerMethodField()

    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    phoneNumber = serializers.CharField(source='phone_number')
    userType = serializers.CharField(source='user_type')
    isSuperuser = serializers.BooleanField(source='is_superuser')

    class Meta:
        model = User
        fields = [
            'id',
            'firstName',
            'lastName',
            'email',
            'phoneNumber',
            'userType',
            'avatarImageUrl',
            'isSuperuser'
        ]

    def get_avatarImageUrl(self, obj):
        if obj.avatar_image:
            return f"{settings.MEDIA_URL}{obj.avatar_image}"
        return None


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    

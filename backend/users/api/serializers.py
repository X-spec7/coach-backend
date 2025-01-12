from rest_framework import serializers

from backend.users.models import User

from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    avatar_image_url = serializers.SerializerMethodField()
    banner_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'full_name', 'phone_number', 'email', 'user_type', 'years_of_experience', 'specialization', 'avatar_image_url', 'banner_image_url']

    def get_avatar_image_url(self, obj):
        if obj.avatar_image:
            return f"{settings.MEDIA_URL}{obj.avatar_image}"
        return None
    
    def get_banner_image_url(self, obj):
        if obj.banner_image:
            return f"{settings.MEDIA_URL}{obj.banner_image}"
        return None


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    

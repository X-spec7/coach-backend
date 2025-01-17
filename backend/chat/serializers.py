from django.conf import settings
from rest_framework import serializers
from backend.chat.models import Contact, Message

class MessageSerializer(serializers.ModelSerializer):
    isRead = serializers.BooleanField(source="is_read")
    sentDate = serializers.DateTimeField(source="timestamp")

    class Meta:
        model = Message
        fields = ["id", "content", "isRead", "sentDate"]

class ContactUserSerializer(serializers.ModelSerializer):
    avatarUrl = serializers.SerializerMethodField()

    fullName = serializers.CharField(source="contact.full_name")
    userType = serializers.CharField(source="contact.user_type")
    lastMessage = MessageSerializer(source="last_message")

    class Meta:
        model = Contact
        fields = ["id", "fullName", "avatarUrl", "userType", "unreadCount", "lastMessage"]

    def get_avatarUrl(self, obj):
        if obj.contact.avatar_image:
            return self.context["request"].build_absolute_uri(obj.contact.avatar_image.url)
        return None


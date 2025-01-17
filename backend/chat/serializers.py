from rest_framework import serializers
from backend.chat.models import Contact, Message

class MessageSerializer(serializers.ModelSerializer):
    isRead = serializers.BooleanField(source="is_read")
    sentDate = serializers.DateTimeField(source="timestamp")

    class Meta:
        model = Message
        fields = ["id", "content", "isRead", "sentDate"]

class ContactUserSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source="contact.full_name")
    avatarUrl = serializers.ImageField(source="contact.avatar_image")
    userType = serializers.CharField(source="contact.user_type")
    lastMessage = MessageSerializer(source="last_message")

    class Meta:
        model = Contact
        fields = ["id", "fullName", "avatarUrl", "userType", "unreadCount", "lastMessage"]

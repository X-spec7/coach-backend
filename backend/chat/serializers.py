from django.conf import settings
from rest_framework import serializers
from backend.chat.models import Contact, Message
from backend.users.models import User

class GetUserSerializer(serializers.ModelSerializer):
    avatarUrl = serializers.SerializerMethodField()
    fullName = serializers.CharField(source="full_name")
    userType = serializers.CharField(source="user_type")

    class Meta:
        model = User
        fields = ["id", "fullName", "avatarUrl", "userType"]

    def get_avatarUrl(self, obj):
        if obj.avatar_image:
            return f"{settings.MEDIA_URL}{obj.avatar_image}"
        return None

class MessageSerializer(serializers.ModelSerializer):
    isRead = serializers.BooleanField(source="is_read")
    sentDate = serializers.DateTimeField(source="timestamp")
    isSent = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "content", "isRead", "isSent", "sentDate"]
    
    def get_isSent(self, obj):
        """Determine if the message was sent by the request user."""
        request_user = self.context.get("request_user")
        return obj.sender == request_user

class ContactUserSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    avatarUrl = serializers.SerializerMethodField()
    fullName = serializers.SerializerMethodField()
    userType = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()
    unreadCount = serializers.IntegerField(source="unread_count")

    class Meta:
        model = Contact
        fields = ["id", "fullName", "avatarUrl", "userType", "unreadCount", "lastMessage"]

    def get_id(self, obj):
        request_user = self.context.get("request_user")
        return obj.user_two.id if obj.user_one == request_user else obj.user_one.id

    def get_other_person(self, obj):
        request_user = self.context.get("request_user")
        return obj.user_two if obj.user_one == request_user else obj.user_one

    def get_avatarUrl(self, obj):
        other_person = self.get_other_person(obj)
        if other_person.avatar_image:
            return f"{settings.MEDIA_URL}{other_person.avatar_image}"
        return None

    def get_fullName(self, obj):
        other_person = self.get_other_person(obj)
        return other_person.full_name

    def get_userType(self, obj):
        other_person = self.get_other_person(obj)
        return other_person.user_type
    
    def get_lastMessage(self, obj):
        if obj.last_message:
            return MessageSerializer(obj.last_message, context=self.context).data
        return None

from django.conf import settings
from rest_framework import serializers
from backend.chat.models import Contact, Message

class MessageSerializer(serializers.ModelSerializer):
    isRead = serializers.BooleanField(source="is_read")
    sentDate = serializers.DateTimeField(source="timestamp")
    isSent = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "content", "isRead", "sentDate"]
    
    def get_isSent(self, obj):
        request_user = self.context.get("request_user")
        return obj.user == request_user

class ContactUserSerializer(serializers.ModelSerializer):
    avatarUrl = serializers.SerializerMethodField()
    fullName = serializers.SerializerMethodField()
    userType = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()
    unreadCount = serializers.IntegerField(source="unread_count")

    class Meta:
        model = Contact
        fields = ["id", "fullName", "avatarUrl", "userType", "unreadCount", "lastMessage"]

    def get_other_person(self, obj):
        request_user = self.context.get("request_user")
        return obj.contact_two if obj.user_one == request_user else obj.user_one

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

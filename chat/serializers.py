from rest_framework import serializers
from .models import ChatRoom, Participant, Message, UserMessageStatus
from backend.users.api.serializers import UserSerializer


class ParticipantSerializer(serializers.ModelSerializer):
    """Serializer for Participant model."""
    user = UserSerializer()

    class Meta:
        model = Participant
        fields = ['id', 'user', 'role', 'join_date', 'is_muted']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'room', 'content', 'timestamp', 'edited']


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for ChatRoom model."""
    members = UserSerializer(many=True, read_only=True)
    participants = ParticipantSerializer(many=True, read_only=True, source='participants_set')
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'is_group', 'members', 'participants', 'unread_count']

    def get_unread_count(self, obj):
        """Calculate the unread message count for the current user in this room."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0


class UserMessageStatusSerializer(serializers.ModelSerializer):
    """Serializer for UserMessageStatus model."""
    message = MessageSerializer()
    unread_message_count = serializers.SerializerMethodField()

    class Meta:
        model = UserMessageStatus
        fields = ['id', 'user', 'message', 'is_read', 'unread_message_count']

    def get_unread_message_count(self, obj):
        """Fetch the count of unread messages for the user across all rooms."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserMessageStatus.objects.filter(user=request.user, is_read=False).count()
        return 0

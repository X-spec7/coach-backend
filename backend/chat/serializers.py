from rest_framework import serializers
from backend.chat.models import ChatRoom, ChatMessage
from backend.users.models import User
from django.conf import settings

class UserForChatSerializer(serializers.ModelSerializer):
    avatar_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'avatar_image_url', 'first_name', 'last_name']

    def get_avatar_image_url(self, obj):
        if obj.avatar_image:
            return f"{settings.MEDIA_URL}{obj.avatar_image}"
        return None
    
class ChatRoomSerializer(serializers.ModelSerializer):
	member = UserForChatSerializer(many=True, read_only=True)
	members = serializers.ListField(write_only=True)

	def create(self, validatedData):
		memberObject = validatedData.pop('members')
		chatRoom = ChatRoom.objects.create(**validatedData)
		chatRoom.member.set(memberObject)
		return chatRoom

	class Meta:
		model = ChatRoom
		exclude = ['id']

class ChatMessageSerializer(serializers.ModelSerializer):
	userName = serializers.SerializerMethodField()
	userImage = serializers.ImageField(source='user.image')

	class Meta:
		model = ChatMessage
		exclude = ['id', 'chat']

	def get_userName(self, Obj):
		return Obj.user.first_name + ' ' + Obj.user.last_name
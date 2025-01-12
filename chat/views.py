from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.pagination import PageNumberPagination
from .models import ChatRoom, Message, UserMessageStatus
from .serializers import ChatRoomSerializer, MessageSerializer
from .tasks import update_unread_counts
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()

class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        chat_rooms = ChatRoom.objects.filter(members=user)
        serializer = ChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ChatRoomDetailView(APIView, PageNumberPagination):
    permission_classes = [AllowAny, ]

    def get(self, request, room_name):
        user = request.user
        chat_room = get_object_or_404(ChatRoom, name=room_name, members=user)
        messages = Message.objects.filter(room=chat_room).order_by('timestamp')
        results = self.paginate_queryset(messages, request, view=self)
        serializer = MessageSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)


class MarkAllMessagesAsReadView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request):
        user = request.user
        unread_messages = UserMessageStatus.objects.filter(user=user, is_read=False)
        unread_messages.update(is_read=True)

        for room in ChatRoom.objects.filter(members=user):
            update_unread_counts.delay(room_name=room.name, sender_id=user.id)

        return Response({"detail": "All unread messages across all rooms marked as read."}, status=HTTP_200_OK)


class SendMessageView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, room_name):
        user = request.user
        content = request.data.get('message', '')

        if not content:
            return Response({"error": "Message content cannot be empty."}, status=HTTP_400_BAD_REQUEST)

        try:
            chat_room = ChatRoom.objects.get(name=room_name, members=user)
            message = Message.objects.create(sender=user, room=chat_room, content=content)
            serializer = MessageSerializer(message)

            update_unread_counts.delay(room_name=room_name, sender_id=user.id)

            return Response(serializer.data, status=HTTP_200_OK)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found or not accessible."}, status=HTTP_400_BAD_REQUEST)


class TypingStatusView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, room_name):
        user = request.user
        typing_status = request.data.get('is_typing', False)

        return Response({
            "detail": f"User {user.id} is {'typing' if typing_status else 'not typing'} in room {room_name}."
        }, status=HTTP_200_OK)


class RoomManagementView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request):
        name = request.data.get('name', '').strip()
        if not name:
            return Response({"error": "Room name cannot be empty."}, status=HTTP_400_BAD_REQUEST)

        if ChatRoom.objects.filter(name=name).exists():
            return Response({"error": "Room with this name already exists."}, status=HTTP_400_BAD_REQUEST)

        chat_room = ChatRoom.objects.create(name=name)
        chat_room.members.add(request.user)
        return Response({"detail": f"Room '{name}' created successfully."}, status=HTTP_200_OK)

    def patch(self, request, room_name):
        user = request.user
        chat_room = get_object_or_404(ChatRoom, name=room_name, members=user)

        description = request.data.get('description', None)
        if description is not None:
            chat_room.description = description
            chat_room.save()

        add_members = request.data.get('add_members', [])
        remove_members = request.data.get('remove_members', [])
        if add_members:
            users_to_add = User.objects.filter(id__in=add_members)
            chat_room.members.add(*users_to_add)
        if remove_members:
            users_to_remove = User.objects.filter(id__in=remove_members)
            chat_room.members.remove(*users_to_remove)

        return Response({"detail": "Room updated successfully."}, status=HTTP_200_OK)


class UnreadNotificationsView(APIView):
    permission_classes = [AllowAny, ]

    def get(self, request):
        user = request.user
        unread_counts = (
            UserMessageStatus.objects.filter(user=user, is_read=False)
            .values('message__room__name')
            .annotate(unread_count=Count('id'))
        )

        data = [
            {"room_name": entry["message__room__name"], "unread_count": entry["unread_count"]}
            for entry in unread_counts
        ]

        return Response(data, status=HTTP_200_OK)


class SearchChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response({"error": "Query parameter cannot be empty."}, status=HTTP_400_BAD_REQUEST)

        user = request.user
        matching_rooms = ChatRoom.objects.filter(name__icontains=query, members=user)
        serializer = ChatRoomSerializer(matching_rooms, many=True)

        return Response(serializer.data, status=HTTP_200_OK)


class DetailedUserChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_name):
        user = request.user
        chat_room = get_object_or_404(ChatRoom, name=room_name, members=user)
        messages = Message.objects.filter(room=chat_room).order_by('timestamp')
        members = chat_room.members.annotate(message_count=Count('messages_sent'))
        results = PageNumberPagination().paginate_queryset(messages, request, view=self)

        data = {
            "messages": MessageSerializer(results, many=True).data,
            "members": [{
                "id": member.id,
                "full_name": member.get_full_name(),
                "avatar": member.avatar_image.url if member.avatar_image else None,
                "message_count": member.message_count
            } for member in members]
        }

        return Response(data, status=HTTP_200_OK)

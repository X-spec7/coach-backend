from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from backend.chat.models import ChatRoom, Message, UserMessageStatus
from .serializers import ChatRoomSerializer, MessageSerializer
from .tasks import update_unread_counts
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()


class AuthorizedUserListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            all_users = User.objects.all()
            print("user list ----->", list(all_users))

            users_info = [
                {
                    "id": user.id,
                    "name": user.get_full_name(),
                    "avatar": user.avatar_image.url if user.avatar_image and hasattr(user.avatar_image, "url") else None,
                }
                for user in all_users
            ]

            return Response({"user": users_info}, status=HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)



class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        chat_rooms = ChatRoom.objects.filter(members=user)
        data = [
            {
                "id": room.id,
                "name": room.name,
                "is_group": room.is_group,
                "member_count": room.members.count(),
            }
            for room in chat_rooms
        ]
        return Response(data, status=HTTP_200_OK)    


class ChatRoomDetailView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        room_name = request.query_params.get('room_name', '').strip()
        if not room_name:
             Response({"error": "room_name is required."}, status=HTTP_400_BAD_REQUEST)

        chat_room = get_object_or_404(ChatRoom, name=room_name, members=user)
        other_person = chat_room.members.exclude(id=user.id).first()

        if not other_person:
            return Response({"error": "No other members found in the chat room."}, status=404)
        
        messages = Message.objects.filter(room=chat_room).order_by('timestamp')
        if not messages.exists():
            return Response({"error": "No messages available in this chat room."}, status=404)
        
        paginated_messages = self.paginate_queryset(messages, request, view=self)
        if paginated_messages is None:
            return Response({"error": "Invalid page number."}, status=404)
        
        serialized_messages = MessageSerializer(paginated_messages, many=True).data

        return Response({
            "room_id": chat_room.id,
            "room_name": chat_room.name,
            "other_person": {
                "id": other_person.id,
                "full_name": other_person.get_full_name(),
                "avatar_url": other_person.avatar_image.url if other_person.avatar_image and hasattr(other_person.avatar_image, "url") else None,
            } if other_person else None,
            "messages": serialized_messages,
        }, HTTP_200_OK)


class MarkAllMessagesAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        unread_messages = UserMessageStatus.objects.filter(user=user, is_read=False)
        unread_messages.update(is_read=True)

        for room in ChatRoom.objects.filter(members=user):
            update_unread_counts.delay(room_name=room.name)

        return Response({"detail": "All unread messages across all rooms marked as read."}, status=HTTP_200_OK)


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        room_name = request.data.get('room_name')
        content = request.data.get('message', '')

        if not content:
            return Response({"error": "Message content cannot be empty."}, status=HTTP_400_BAD_REQUEST)

        try:
            chat_room = ChatRoom.objects.get(name=room_name, members=user)
            message = Message.objects.create(sender=user, room=chat_room, content=content)
            serializer = MessageSerializer(message)

            update_unread_counts.delay(room_name=room_name)

            return Response(serializer.data, status=HTTP_200_OK)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found or not accessible."}, status=HTTP_400_BAD_REQUEST)


class TypingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        room_name = request.data.get('room_name')
        typing_status = request.data.get('is_typing', False)

        return Response({"detail": f"User {user.id} is {'typing' if typing_status else 'not typing'} in room {room_name}."}, status=HTTP_200_OK)
    

class RoomManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            add_members = request.data.get('add_members', [])
            target_user_id = request.data.get('target_user_id', None)

            if target_user_id:
                try:
                    target_user = User.objects.get(id=target_user_id)
                except User.DoesNotExist:
                    return Response({"error": "Target user not found."}, status=HTTP_404_NOT_FOUND)
                
                room_name = f"chat_{min(request.user.id, target_user.id)}_{max(request.user.id, target_user.id)}"

                existing_room = ChatRoom.objects.filter(
                    members=request.user
                ).filter(members=target_user).first()

                if existing_room:
                    return Response({
                        "detail": "Room already exists.",
                        "room_id": existing_room.id,
                        "room_name": existing_room.name
                    }, status=HTTP_200_OK)

                chat_room = ChatRoom.objects.create(name=room_name)
                chat_room.members.add(request.user, target_user)
            else:
                room_name = request.data.get('name', '').strip()
                if not room_name:
                    return Response({"error": "Room name cannot be empty."}, status=HTTP_400_BAD_REQUEST)

                if ChatRoom.objects.filter(name=room_name).exists():
                    return Response({"error": "Room with this name already exists."}, status=HTTP_400_BAD_REQUEST)

                chat_room = ChatRoom.objects.create(name=room_name)
                chat_room.members.add(request.user)

                if add_members:
                    users_to_add = User.objects.filter(id__in=add_members)
                    chat_room.members.add(*users_to_add)

            return Response(
                {"detail": f"Room '{chat_room.name}' created successfully.", "room_id": chat_room.id, "room_name": chat_room.name},
                status=HTTP_200_OK,
            )
        except AttributeError as attr_err:
            return Response({"error": f"Attribute error: {str(attr_err)}"}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."}, status=HTTP_500_INTERNAL_SERVER_ERROR)


class UnreadNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

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


class SearchUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        user = request.user

        if not query:
            chatted_user_ids = ChatRoom.objects.filter(members=user).values_list('members', flat=True).distinct()
            users = User.objects.filter(id__in=chatted_user_ids).exclude(id=user.id)
        else:
            users = User.objects.filter(
                Q(full_name__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            
        users_data = []
        for u in users:
            last_message = Message.objects.filter(
                Q(sender=u, room__members=user) | Q(room__members=u, sender=user)
            ).order_by('-timestamp').first()
            unread_count = UserMessageStatus.objects.filter(user=user, message__sender=u, is_read=False).count()

            last_message_data = {
                "id": str(last_message.id) if last_message else None,
                "content": last_message.content if last_message else None,
                "isRead": not unread_count if last_message else None,
                "isSent": last_message.sender == user if last_message else None,
                "sentDate": last_message.timestamp.isoformat() if last_message else None,
            } if last_message else None

            users_data.append({
                "id": u.id,
                "fullName": u.full_name,
                "avatarUrl": u.avatar_image.url if u.avatar_image and hasattr(u.avatar_image, "url") else None,
                "userType": u.user_type,
                "unreadCount": unread_count,
                "lastMessage": last_message_data
            })

        return Response(users_data, status=HTTP_200_OK)
    

class ChatSidebarView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user

        chat_rooms = ChatRoom.objects.filter(members=user).distinct()
        
        user_data = []
        for room in chat_rooms:
            other_person = room.members.exclude(id=user.id).first()

            if other_person:
                last_message = Message.objects.filter(room=room).order_by('-timestamp').first()

                unread_count = UserMessageStatus.objects.filter(
                    user=user, message__room=room, is_read=False
                ).count()

                user_data.append({
                    "id": other_person.id,
                    "fullName": other_person.get_full_name(),
                    "avatarUrl": other_person.avatar_image.url if other_person.avatar_image and hasattr(other_person.avatar_image, "url") else None,
                    "userType": other_person.user_type,
                    "unreadCount": unread_count,
                    "lastMessage": {
                        "id": str(last_message.id) if last_message else None,
                        "content": last_message.content if last_message else None,
                        "isRead": not unread_count if last_message else None,
                        "isSent": last_message.sender == user if last_message else None,
                        "sentDate": last_message.timestamp.isoformat() if last_message else None,
                    } if last_message else None
                })
        
        return Response(user_data, status=HTTP_200_OK)


class ChatWithUserDetailView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        target_user_id = request.query_params.get('user_id', '').strip()
        
        if not target_user_id:
            return Response({"error": "User ID is required."}, status=HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({"error": "Target user not found."}, status=HTTP_404_NOT_FOUND)
        
        chat_room = ChatRoom.objects.filter(members=user).filter(members=target_user).first()
        if not chat_room:
            return Response({"error": "Chat room not found for the given user."}, status=HTTP_404_NOT_FOUND)
        messages = Message.objects.filter(room=chat_room).order_by('timestamp')
        paginated_messages = self.paginate_queryset(messages, request, view=self)

        total_message_count = Message.objects.filter(room=chat_room).count()

        if not paginated_messages:
            formatted_messages = []
        else:
            formatted_messages = [
                {
                    "id": str(message.id),
                    "content": message.content,
                    "isRead": UserMessageStatus.objects.filter(user=user, message=message, is_read=True).exists(),
                    "isSent": message.sender == user,
                    "sentDate": message.timestamp.isoformat(),
                } for message in paginated_messages
            ]
        
        return Response({
            "room_id": chat_room.id,
            "room_name": chat_room.name,
            "other_person": {
                "id": target_user.id,
                "full_name": target_user.get_full_name(),
                "avatar_url": target_user.avatar_image.url if target_user.avatar_image and hasattr(target_user.avatar_image, "url") else None,
            },
            "messages": formatted_messages,
            "totalMessageCount": total_message_count,
        }, status=HTTP_200_OK)

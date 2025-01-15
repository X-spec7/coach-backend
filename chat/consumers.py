import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from backend.chat.models import ChatRoom, Message, UserMessageStatus
from .serializers import MessageSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, DatabaseError
from django.dispatch import Signal, receiver
from .tasks import update_unread_counts, send_notification_to_group
from .utils import CacheUtility
from asgiref.sync import sync_to_async

User = get_user_model()

message_saved = Signal()
message_read = Signal()

cache_utility = CacheUtility()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        try:
            print("this is whole scope", self.scope)
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            if not self.room_name:
                print("Room name missing in URL route.")
                await self.close()
                return
            self.room_group_name = f"chat_{self.room_name}"

            # Ensure the user is authenticated
            user = self.scope.get("user")
            if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
                print("User not authenticated or user is None.")
                await self.close()
                return

            print(f"User in scope: {user}")

            self.sender_username = self.user.get_username()


            print(f"User {self.user.pk} connected, adding {self.channel_name} to {self.sender_username}")

            # Fetch the chat room
            try:
                room = await (ChatRoom.objects.prefetch_related("members").get)(name=self.room_name)
            except ChatRoom.DoesNotExist:
                print(f"No room found with name: {self.room_name}")
                await self.close()
                return

            # Verify membership
            is_member = await sync_to_async(room.members.filter(id=user.id).exists)()
            print("am I member?", is_member)
            if not is_member:
                print(f"User {user.id} is not a member of the room {self.room_name}.")
                await self.close()
                return

            # Add user to the group and accept the WebSocket connection
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            # Fetch unread count and send notification
            unread_count = await self.get_total_unread_count(user.id)
            await self.send(json.dumps({
                "type": "notification",
                "unread_count": unread_count
            }))

        except Exception as e:
            print(f"Error during WebSocket connection: {e}")
            await self.close()


    async def disconnect(self, close_code):
        print("websocket was disconnetected")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user_id = self.scope['user'].id
        message_type = data.get('type', 'chat')

        try:
            if message_type == 'chat':
                message_instance = await self.save_message(self.room_name, user_id, message)

                await sync_to_async(message_saved.send)(
                    sender=self.__class__, room=message_instance.room, user=message_instance.sender
                )

                serialized_message = MessageSerializer(message_instance).data

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': serialized_message
                    }
                )

                update_unread_counts.delay(room_name=self.room_name, sender_id=user_id)

            elif message_type == 'system':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'system_notification',
                        'message': message
                    }
                )

            elif message_type == 'typing':
                typing_status = data.get('status', False)

                user_name = await sync_to_async(self.scope['user'].get_full_name)()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user': self.scope['user'].id,
                        'status': typing_status
                    }
                )

        except ObjectDoesNotExist:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Room or user does not exist.'
            }))

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def system_notification(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': message
        }))

    async def typing_indicator(self, event):
        user = event['user']
        status = event['status']

        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user': user,
            'status': status
        }))

    @sync_to_async
    def save_message(self, room_name, user_id, message):
        try:
            with transaction.atomic():
                user = User.objects.get(id=user_id)
                room = ChatRoom.objects.get(name=room_name)
                message_instance = Message.objects.create(
                    sender=user,
                    room=room,
                    content=message
                )

                unread_statuses = [
                    UserMessageStatus(
                        user=participant,
                        message=message_instance,
                        is_read=False
                    )
                    for participant in room.members.exclude(id=user_id)
                ]
                UserMessageStatus.objects.bulk_create(unread_statuses)

                send_notification_to_group.delay(
                    room_name=self.room_name,
                    message_id=message_instance.id
                )

                return message_instance

        except (ObjectDoesNotExist, DatabaseError):
            raise

    @sync_to_async
    def mark_message_as_read(self, user_id, message_id):
        try:
            with transaction.atomic():
                status = UserMessageStatus.objects.get(user_id=user_id, message_id=message_id)
                status.is_read = True
                status.save()

                cache_key = f'unread_count_{user_id}'
                unread_count = UserMessageStatus.objects.filter(user_id=user_id, is_read=False).count()
                cache_utility.set(cache_key, unread_count, timeout=3600)

        except ObjectDoesNotExist:
            pass

    @sync_to_async
    def get_total_unread_count(self, user_id):
        async def fetch_unread_count():
            cache_key = f'unread_count_{user_id}'
            unread_count = await cache_utility.get(cache_key)  # Await the async get method
            if unread_count is None:
                unread_count = UserMessageStatus.objects.filter(user_id=user_id, is_read=False).count()
                await cache_utility.set(cache_key, unread_count, timeout=3600)
            return unread_count
        
        return asyncio.run(fetch_unread_count())

@receiver(message_saved)
def handle_message_saved(sender, room, user, **kwargs):
    print(f"Message saved in room {room} by user {user}")

@receiver(message_read)
def handle_message_read(sender, user, message, **kwargs):
    print(f"Message {message} read by user {user}")

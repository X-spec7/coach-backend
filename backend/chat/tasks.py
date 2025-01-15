from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count
from channels.db import database_sync_to_async
from backend.chat.models import ChatRoom, UserMessageStatus, Message
from .utils import CacheUtility
import json

User = get_user_model()

cache_utility = CacheUtility()

@shared_task
def update_unread_counts(room_name, sender_id):
    try:
        room = ChatRoom.objects.prefetch_related('members').get(name=room_name)

        unread_counts = (
            UserMessageStatus.objects.filter(message__room=room, is_read=False)
            .values('user_id')
            .annotate(unread_count=Count('id'))
        )

        for entry in unread_counts:
            cache_key = f'unread_count_{entry["user_id"]}'
            database_sync_to_async(cache_utility.set)(cache_key, entry["unread_count"], timeout=3600)

    except ChatRoom.DoesNotExist:
        print(f"Room {room_name} does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred in update_unread_counts: {e}")


@shared_task
def send_notification_to_group(room_name, message_id):
    try:
        message = Message.objects.select_related('sender').get(id=message_id)

        notification = {
            'type': 'new_message',
            'message_id': message.id,
            'room_name': room_name,
            'sender': message.sender.full_name,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
        }

        notification_json = json.dumps(notification)
        database_sync_to_async(cache_utility.publish)(f'notification_channel_{room_name}', notification_json)

    except Message.DoesNotExist:
        print(f"Message with ID {message_id} does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred in send_notification_to_group: {e}")

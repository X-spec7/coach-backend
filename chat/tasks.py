from celery import shared_task
from django.contrib.auth import get_user_model
from .models import ChatRoom, UserMessageStatus
from .utils import CacheUtility
import json

User = get_user_model()

cache_utility = CacheUtility()

@shared_task
def update_unread_counts(room_name, sender_id):
    try:
        room = ChatRoom.objects.prefetch_related('members').get(name=room_name)
        sender = User.objects.get(id=sender_id)

        for participant in room.members.exclude(id=sender_id):
            unread_count = UserMessageStatus.objects.filter(user=participant, is_read=False).count()
            cache_key = f'unread_count_{participant.id}'
            cache_utility.set(cache_key, unread_count, timeout=3600)

    except ChatRoom.DoesNotExist:
        print(f"Room {room_name} does not exist.")
    except User.DoesNotExist:
        print(f"User with ID {sender_id} does not exist.")

@shared_task
def send_notification_to_group(room_name, message_id):
    try:
        room = ChatRoom.objects.prefetch_related('members').get(name=room_name)

        notification = {
            'type': 'new_message',
            'message_id': message_id,
            'room_name': room_name
        }

        notification_json = json.dumps(notification)
        cache_utility.publish(f'notification_channel_{room_name}', notification_json)

    except ChatRoom.DoesNotExist:
        print(f"Room {room_name} does not exist.")

import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

from channels.db import database_sync_to_async
from django.utils.timezone import now
from backend.chat.models import Message, Contact
from backend.users.models import User
from asgiref.sync import async_to_sync

def sanitize_group_name(name: str) -> str:
    # Replace all invalid characters with an underscore
    return re.sub(r"[^a-zA-Z0-9_\-.]", "_", name)[:100]

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['userId']
        user = User.objects.get(id=user_id)
        self.user = user
        self.user_id = user_id

        self.group_name = sanitize_group_name(f"group_{user.uuid}")
        async_to_sync (self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    # async def disconnect(self, close_code):
        # if self.user.is_authenticated:
        #     await self.channel_layer.group_discard(f"user_{self.user.id}", self.channel_name)
        #     await self.set_user_status("offline")

    def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")
        if message_type == "send_message":
            self.handle_send_message(data)
        elif message_type == "initiate_call":
            self.handle_initiate_call(data)
        elif message_type == "accept_call":
            self.handle_accept_call(data)
        elif message_type == "decline_call":
            self.handle_decline_call(data)
        elif message_type == "cancel_call":
            self.handle_cancel_call(data)
        elif message_type == "busy":
            self.handle_busy(data)
        # elif message_type == "is_typing":
        #     await self.handle_typing_status(content)

    def handle_send_message(self, data):
        recipient_id = data.get("recipient_id")
        message = data.get("message")
        recipient = User.objects.get(id=recipient_id)
        new_message = Message.objects.create(
            sender=self.user, recipient=recipient, content=message
        )

        # Update contact last message and unread count
        self.update_contact(new_message)

        receiver_group_name = sanitize_group_name(f"group_{recipient.uuid}")

        async_to_sync (self.channel_layer.group_send)(
            receiver_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": new_message.id,
                    "content": new_message.content,
                    "isRead": new_message.is_read,
                    "isSent": False,
                    "sentDate": new_message.timestamp.isoformat(),
                },
            },
        )

        async_to_sync (self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": new_message.id,
                    "content": new_message.content,
                    "isRead": new_message.is_read,
                    "isSent": True,
                    "sentDate": new_message.timestamp.isoformat(),
                },
            },
        )


    def handle_initiate_call(self, data):
        recipient_id = data.get("otherPersonId")
        meeting_link = data.get("meetingLink")
        other_person_avatar_url = data.get("otherPersonAvatarUrl")
        other_person_name = data.get("otherPersonName")

        recipient = User.objects.get(id=recipient_id)
        receiver_group_name = sanitize_group_name(f"group_{recipient.uuid}")

        async_to_sync (self.channel_layer.group_send)(
            receiver_group_name,
            {
                "type": "initiate_call",
                "callInfo": {
                    "otherPersonId": self.user_id,
                    "meetingLink": meeting_link,
                    "otherPersonAvatarUrl": other_person_avatar_url,
                    "otherPersonName": other_person_name,
                },
            }
        )

    def handle_accept_call(self, data):
        recipient_id = data.get("otherPersonId")
        recipient = User.objects.get(id=recipient_id)
        receiver_group_name = sanitize_group_name(f"group_{recipient.uuid}")

        async_to_sync (self.channel_layer.group_send)(
            receiver_group_name,
            {
                "type": "accept_call"
            }
        )
    
    def handle_decline_call(self, data):
        recipient_id = data.get("otherPersonId")
        recipient = User.objects.get(id=recipient_id)
        receiver_group_name = sanitize_group_name(f"group_{recipient.uuid}")

        async_to_sync (self.channel_layer.group_send)(
            receiver_group_name,
            {
                "type": "decline_call"
            }
        )
    
    def handle_cancel_call(self, data):
        recipient_id = data.get("otherPersonId")
        recipient = User.objects.get(id=recipient_id)
        receiver_group_name = sanitize_group_name(f"group_{recipient.uuid}")

        async_to_sync (self.channel_layer.group_send)(
            receiver_group_name,
            {
                "type": "cancel_call"
            }
        )

    def handle_busy(self, data):
        recipient_id = data.get("otherPersonId")
        recipient = User.objects.get(id=recipient_id)
        receiver_group_name = sanitize_group_name(f"group_{recipient.uuid}")

        async_to_sync (self.channel_layer.group_send)(
            receiver_group_name,
            {
                "type": "busy"
            }
        )
    
    def chat_message(self, event):
        message = event['message']
        print(f"event ------> {event}")

        self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message
        }))

    def initiate_call(self, event):
        callInfo = event['callInfo']
        print(f"call info ------> {callInfo}")

        self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'callInfo': callInfo
        }))
    
    def accept_call(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_accepted'
        }))
    
    def decline_call(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_declined'
        }))

    def cancel_call(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_cancelled'
        }))
    
    def busy(self, event):
        self.send(text_data=json.dumps({
            'type': 'busy'
        }))

    def update_contact(self, message):
        # Ensure user_one is the smaller ID and user_two is the larger ID
        user_one, user_two = (
            (message.sender, message.recipient)
            if message.sender.id < message.recipient.id
            else (message.recipient, message.sender)
        )
        
        # Get or create the contact
        contact, created = Contact.objects.get_or_create(
            user_one=user_one,
            user_two=user_two,
            defaults={
                "last_message": message,
                "unread_count": 1 if message.recipient == user_two else 0,
            }
        )

        # Update the contact's last message and unread count
        if not created:
            contact.last_message = message
            if message.recipient == user_two:
                contact.unread_count += 1
            contact.save()

    # def handle_typing_status(self, content):
    #     recipient_id = content.get("recipient_id")
    #     is_typing = content.get("is_typing", False)

    #     # Notify the recipient of typing status
    #     self.channel_layer.group_send(
    #         f"user_{recipient_id}",
    #         {
    #             "type": "typing_status",
    #             "user_id": self.user.id,
    #             "is_typing": is_typing,
    #         },
    #     )

    # def typing_status(self, event):
    #     self.send_json({
    #         "type": "typing_status",
    #         "user_id": event["user_id"],
    #         "is_typing": event["is_typing"],
    #     })


    # def set_user_status(self, status):
    #     self.user.status = status
    #     self.user.last_seen = now()
    #     self.user.save()

    # def chat_message(self, event):
    #     print("sending back")
    #     self.send(event["message"])

from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from asgiref.sync import sync_to_async, async_to_sync
from backend.chat.models import Message, Contact
from backend.users.models import User
class ChatConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['userId']
        user = User.objects.get(id=user_id)
        async_to_sync (self.channel_layer.group_add)(
            str(user.uuid),
            self.channel_name
        )

        self.accept()

    # async def disconnect(self, close_code):
        # if self.user.is_authenticated:
        #     await self.channel_layer.group_discard(f"user_{self.user.id}", self.channel_name)
        #     await self.set_user_status("offline")

    def receive(self, data):
        message_type = data.get("type")
        if message_type == "send_message":
            self.handle_send_message(data)
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

        async_to_sync (self.channel_layer.group_send)(
            recipient.uuid,
            {
                "type": "chat_message",
                "message": {
                    "id": new_message.id,
                    "content": new_message.content,
                    "isRead": new_message.is_read,
                    "recipientId": recipient_id,
                    "sentDate": new_message.timestamp.isoformat(),
                },
            },
        )

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

    # def set_user_status(self, status):
    #     self.user.status = status
    #     self.user.last_seen = now()
    #     self.user.save()

    # def chat_message(self, event):
    #     self.send_json(event["message"])

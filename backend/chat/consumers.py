from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils.timezone import now
from asgiref.sync import sync_to_async
from backend.chat.models import Message, Contact
from backend.users.models import User
class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            await self.channel_layer.group_add(f"user_{self.user.id}", self.channel_name)
            await self.accept()
            await self.set_user_status("online")

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(f"user_{self.user.id}", self.channel_name)
            await self.set_user_status("offline")

    async def receive_json(self, content):
        message_type = content.get("type")
        if message_type == "send_message":
            await self.handle_send_message(content)
        elif message_type == "is_typing":
            await self.handle_typing_status(content)

    async def handle_send_message(self, content):
        recipient_id = content.get("recipient_id")
        message = content.get("message")
        recipient = await sync_to_async(User.objects.get)(id=recipient_id)
        new_message = await sync_to_async(Message.objects.create)(
            sender=self.user, recipient=recipient, content=message
        )
        # Update contact last message and unread count
        await self.update_contact(new_message)

        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                "type": "chat_message",
                "message": {
                    "id": new_message.id,
                    "content": new_message.content,
                    "isRead": new_message.is_read,
                    "sentDate": new_message.timestamp.isoformat(),
                },
            },
        )

    async def handle_typing_status(self, content):
        recipient_id = content.get("recipient_id")
        is_typing = content.get("is_typing", False)

        # Notify the recipient of typing status
        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                "type": "typing_status",
                "user_id": self.user.id,
                "is_typing": is_typing,
            },
        )

    async def typing_status(self, event):
        await self.send_json({
            "type": "typing_status",
            "user_id": event["user_id"],
            "is_typing": event["is_typing"],
        })

    @sync_to_async
    def update_contact(self, message):
        contact, created = Contact.objects.get_or_create(
            user=message.recipient, contact=message.sender
        )
        contact.last_message = message
        contact.unread_count += 1
        contact.save()

    @sync_to_async
    def set_user_status(self, status):
        self.user.status = status
        self.user.last_seen = now()
        self.user.save()

    async def chat_message(self, event):
        await self.send_json(event["message"])

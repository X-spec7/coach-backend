from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now

User = get_user_model()

# Chatting models
class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    members = models.ManyToManyField(User, through="Participant", related_name="chat_rooms")

    def __str__(self):
        return self.name if self.name else f"Room {self.id}"

    def get_unread_count(self, user):
        from django.db.models import Q

        return UserMessageStatus.objects.filter(
            Q(user=user) & Q(message__room=self) & Q(is_read=False)
        ).count()


class Participant(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="participations")
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="participants")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    join_date = models.DateTimeField(default=now)
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "room")

    def __str__(self):
        return f"{self.user} in {self.room} ({self.role})"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name="messages_sent", on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=now)
    edited = models.BooleanField(default=False)

    def __str__(self):
        return f"Message {self.id} from {self.sender}"


class UserMessageStatus(models.Model):
    user = models.ForeignKey(User, related_name="message_statuses", on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name="user_statuses", on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message {self.message.id} read by {self.user}: {self.is_read}"
from django.db import models
from backend.users import User
from django.utils.translation import gettext_lazy as _

class Message(models.Model):
  sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
  recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
  content = models.TextField(_("Message Content"))
  is_read = models.BooleanField(_("Is Read"), default=False)
  timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)

  def __str__(self):
    return f"From {self.sender} to {self.recipient}: {self.content[:20]}"

class Contact(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contacts")
  contact = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reverse_contacts")
  last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name="contact_last_message")
  unread_count = models.PositiveIntegerField(_("Unread Messages Count"), default=0)

  class Meta:
    unique_together = ("user", "contact")

  def __str__(self):
    return f"{self.user} ↔ {self.contact}"
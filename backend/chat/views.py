from django.db import models
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.chat.models import Contact, Message
from .serializers import ContactUserSerializer, MessageSerializer

class ContactListView(APIView):
    def get(self, request):
        user = request.user
        contacts = Contact.objects.filter(user=user).select_related("contact", "last_message")
        serializer = ContactUserSerializer(contacts, many=True)
        return Response(serializer.data)
    
class MessageListView(ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        other_person_id = self.kwargs["other_person_id"]
        return Message.objects.filter(
            (models.Q(sender=user) & models.Q(recipient_id=other_person_id)) |
            (models.Q(sender_id=other_person_id) & models.Q(recipient=user))
        ).order_by("-timestamp")
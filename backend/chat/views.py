from django.db import models
from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.chat.models import Contact, Message
from .serializers import ContactUserSerializer, MessageSerializer

class ContactListView(APIView):
    def get(self, request):
        user = request.user

        contacts = Contact.objects.filter(
            Q(user_one=user) | Q(contact_two=user)
        ).select_related("user_one", "contact_two", "last_message")

        serializer = ContactUserSerializer(contacts, many=True, context={"request_user": user})
        return Response(serializer.data)
    
class MessageListView(ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        other_person_id = self.kwargs["otherPersonId"]
        return Message.objects.filter(
            (models.Q(sender=user) & models.Q(recipient_id=other_person_id)) |
            (models.Q(sender_id=other_person_id) & models.Q(recipient=user))
        ).order_by("-timestamp")
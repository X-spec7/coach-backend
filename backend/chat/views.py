import traceback
from django.db import models
from django.db.models import Q
from rest_framework import status
from backend.chat.models import Contact, Message
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from backend.users.models import User
from .serializers import (
  ContactUserSerializer,
  MessageSerializer,
  GetUserSerializer,
)
from .dto import GetUsersListDTO

class ContactListView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    user = request.user

    contacts = Contact.objects.filter(
      Q(user_one=user) | Q(user_two=user)
    ).select_related("user_one", "user_two", "last_message")

    try:
      serializer = ContactUserSerializer(contacts, many=True, context={"request_user": user})
      return Response(
        {
          "message": "Contact List Fetched",
          "contacts": serializer.data,
        },
        status=status.HTTP_200_OK
      )
    except Exception as e:
      return Response(
        {"error": "Failed to fetch session count", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
      
class UsersListView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):

    serializer = GetUsersListDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"error": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
        
    validated_data = serializer.validated_data

    limit = validated_data.get("limit", 10)
    offset = validated_data.get("offset", 0)
    query = validated_data.get("query", None)

    try:
      userlists_query = User.objects.all()

      if query:
        userlists_query = userlists_query.filter(full_name__icontains=query)
      
      total_users = userlists_query.count()

      userlists_query = userlists_query[offset:offset + limit]

      users_list = GetUserSerializer(userlists_query, many=True).data

      return Response(
        {
          "message": "Users fetched successfully.",
          "users": users_list,
          "totalUsersCount": total_users
        },
        status=status.HTTP_200_OK
      )
    
    except AttributeError as e:
      print("AttributeError:", str(e))
      traceback.print_exc()
      return Response(
        {"error": "Attribute error occurred", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

    except Exception as e:
      return Response(
        {"error": "Failed to fetch session data", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
class MessageListView(ListAPIView):
  serializer_class = MessageSerializer

  def get_queryset(self):
    user = self.request.user
    other_person_id = self.kwargs["otherPersonId"]

    queryset = Message.objects.filter(
      (models.Q(sender=user.id) & models.Q(recipient=other_person_id)) |
      (models.Q(sender=other_person_id) & models.Q(recipient=user.id))
    ).order_by("-timestamp")

    return queryset

  def list(self, request, *args, **kwargs):
    other_person_id = self.kwargs["otherPersonId"]
    
    queryset = self.get_queryset()

    offset = int(request.query_params.get("offset", 0))
    limit = int(request.query_params.get("limit", 20))

    try:
      other_person = User.objects.get(id=other_person_id)
    except User.DoesNotExist:
      return Response(
          {"message": "Other person not found."},
          status=status.HTTP_404_NOT_FOUND,
      )

    other_person_data = GetUserSerializer(other_person).data

    paginated_queryset = queryset[offset : offset + limit]

    serializer = self.get_serializer(
      paginated_queryset, many=True, context={"request_user": request.user}
    )

    response_data = {
      "totalMessageCount": queryset.count(),
      "messages": serializer.data,
      "otherPersonFullname": other_person_data.get("fullName"),
      "otherPersonAvatarUrl": other_person_data.get("avatarUrl"),
    }

    return Response(
      {"message": "Message fetched successfully", "data": response_data},
      status=status.HTTP_200_OK
    )

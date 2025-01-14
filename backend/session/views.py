import os
import requests
import base64
from django.shortcuts import render
from django.db.models import Max
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

from backend.session.models import Session, Meeting
from django.conf import settings
from .dto import GetSessionsRequestDTO
from .util import create_zoom_meeting

logger = logging.getLogger(__name__)

class GetSessionsView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    # Deserialize the request data using the provided DTO
    serializer = GetSessionsRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"error": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data
    print(f"validated data: {validated_data}")
    limit = validated_data.get("limit", 10)
    offset = validated_data.get("offset", 0)
    goal = validated_data.get("goal", None)
    booked = validated_data.get("booked", None)
    query = validated_data.get("query", None)

    print(f"limit {limit}")
    # limit = validated_data.limit
    # offset = validated_data.offset
    # goal = validated_data.goal
    # booked = validated_data.booked
    # query = validated_data.query

    try:
      print(f"started to get session")
      # Base query set for all sessions
      sessions_query = Session.objects.all()

      print(f"session query {sessions_query}")

      # Apply filtering based on goal if provided
      if goal:
        sessions_query = sessions_query.filter(goal__icontains=goal)

      # Apply query filtering based on title
      if query:
        sessions_query = sessions_query.filter(title__icontains=query)

      # Apply filtering based on booked status (only if booked=True)
      if booked is True:  # If booked is True, filter sessions where the user is in booked_users
        user = request.user  # Get the authenticated user
        sessions_query = sessions_query.filter(booked_users=user)
      
      # Apply pagination (limit and offset)
      sessions_query = sessions_query[offset:offset + limit]

      # Serialize the filtered sessions data in the required format
      session_data = [
        {
          "id": session.id,
          "title": session.title,
          "startDate": session.start_date.isoformat(),  # Ensure the startDate is in ISO format (string)
          "duration": session.duration,
          "coachId": session.coach.id,  # The ID of the coach
          "coachFullname": f"{session.coach.first_name} {session.coach.last_name}",  # Assuming the User model has first and last name
          "goal": session.goal,
          "level": session.level,
          "description": session.description,
          "bannerImageUrl": session.banner_image_url or "",
          "totalParticipantNumber": session.total_participant_number,
          "currentParticipantNumber": session.booked_users.count(),  # The count of booked users
          "price": session.price,
          "equipments": session.equipments or [],  # Ensure it's an empty list if no equipment is provided
          "meetingId": session.meeting.id,  # Assuming meeting is a ForeignKey with an ID field
          "booked": request.user in session.booked_users.all()
        }
        for session in sessions_query
      ]

      return Response(
        {
          "message": "Sessions fetched successfully.",
          "sessions": session_data,
          "pagination": {
            "limit": limit,
            "offset": offset,
            "total_sessions": sessions_query.count()
          }
        },
        status=status.HTTP_200_OK
      )

    except Exception as e:
      return Response(
        {"error": "Failed to fetch session data", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
  
class CreateSessionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        data = request.data
        user = request.user

        title = data['title']
        startDate = data['startDate']
        duration = data['duration']
        description = data['description']
        goal = data['goal']
        level = data['level']
        totalParticipantNumber = data['totalParticipantNumber']
        price = data['price']
        equipments = data.get('equipments', [])

        max_session_id = Session.objects.aggregate(Max('id'))['id__max']

        bannerImageBase64 = data.get('bannerImage')
        print(f" banner image {bannerImageBase64}")

        banner_image_url = None 
        if bannerImageBase64:
            # Decode the Base64 string
            format, imgstr = bannerImageBase64.split(';base64,')  # Split format and data
            ext = format.split('/')[-1]  # Extract the image file extension (e.g., jpg, png)
            if max_session_id is not None:
                file_name = f"{max_session_id}_session_banner.{ext}"
            else:
                file_name = f"1_session_banner.{ext}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'session_banner_images', file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists

            # Save the file
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(imgstr))
            banner_image_url = f"session_banner_images/{file_name}"
        try:
            createMeetingPayload = {
                'topic': title,
                'agenda': description,
                'start_time': startDate,
                'duration': duration,
                'type': 2,
                'settings': {
                    'join_before_host': True,
                },
                'user_id': 'me'
            }

            zoomRes = create_zoom_meeting(createMeetingPayload)

            meeting = Meeting.objects.create(
                start_time=zoomRes.get('start_time'),
                duration=zoomRes.get('duration'),
                meeting_number=zoomRes.get('id'),
                encrypted_password=zoomRes.get('encrypted_password'),
                join_url=zoomRes.get('join_url'),
                start_url=zoomRes.get('start_url'),
                creator=user,
            )
            meeting.save()

            session = Session.objects.create(
                title=title,
                start_date=startDate,
                duration=duration,
                coach=user,
                goal=goal,
                level=level,
                total_participant_number=totalParticipantNumber,
                equipments=equipments,
                price=price,
                meeting=meeting,
            )

            if banner_image_url and banner_image_url != "":
               session.banner_image_url = banner_image_url

            session.save()

            return Response(
                {
                    "message": "session created successfully",
                    "session": session.id,
                    "meeting": meeting.id
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return Response(
                {"error": "Failed to create session"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateMeetingView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
      try:
        createMeetingPayload = {
          'type': 1,
          'settings': {
            'join_before_host': True,
          },
          'user_id': "me"
        }
        zoomRes = create_zoom_meeting(createMeetingPayload)

        return Response(
          {"message": "Created Meeting", "data": zoomRes},
          status=status.HTTP_201_CREATED,
        )
      except Exception as e:
        print(e)
        return Response(
            {"error": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Session
from .dto import GetSessionsRequestDTO

class GetSessionsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            # Deserialize the request data using the provided DTO
            serializer = GetSessionsRequestDTO(data=request.query_params)  # Use query params for GET request

            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid request data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            limit = validated_data.get("limit", 10)  # Default to 10 sessions if no limit is provided
            offset = validated_data.get("offset", 0)  # Default to 0 offset if no offset is provided
            goal = validated_data.get("goal", None)
            booked = validated_data.get("booked", None)
            query = validated_data.get("query", None)

            # Base query set for all sessions
            sessions_query = Session.objects.all()

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
                  "startDate": session.startDate.isoformat(),  # Ensure the startDate is in ISO format (string)
                  "duration": session.duration,
                  "coachId": session.coach.id,  # The ID of the coach
                  "coachFullname": f"{session.coach.first_name} {session.coach.last_name}",  # Assuming the User model has first and last name
                  "goal": session.goal,
                  "level": session.level,
                  "description": session.description,
                  "bannerImageUrl": session.banner_image_url,  # Assuming this field exists in the Session model
                  "totalParticipantNumber": session.totalParticipantNumber,
                  "currentParticipantNumber": session.booked_users.count(),  # The count of booked users
                  "price": session.price,
                  "equipments": session.equipments or [],  # Ensure it's an empty list if no equipment is provided
                  "meetingId": str(session.meeting.id),  # Assuming meeting is a ForeignKey with an ID field
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
                {"error": "Failed to fetch session data", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

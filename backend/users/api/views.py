import os
import requests
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, login
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_ratelimit.decorators import ratelimit

from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser

from backend.users.models import User, Qualification

from .serializers import UserSerializer, LoginSerializer

def send_mail(email, content):
    apiKey = os.getenv("ELASTIC_API_KEY")
    registeredEmail = os.getenv("ElASTIC_REGISTERED_EMAIL")

    print("api key: ", apiKey)
    print("registered email: ", registeredEmail)

    email_params = {
        "apikey": os.getenv("ELASTIC_API_KEY"),
        "from": os.getenv("ElASTIC_REGISTERED_EMAIL"),
        "to": email,
        "subject": "Email Verify - Coach Account",
        "bodyHtml": f"{content}",
        # "isTransactional": True,
    }

    response = requests.post(
        "https://api.elasticemail.com/v2/email/send",
        data=email_params,
    )
    return response

def send_mailgun_mail(to_mail, content):
    try:
        MAILGUN_API_URL = "https://api.mailgun.net/v3/sandbox5023f2da06d8495cbcb235139417e7bf.mailgun.org/messages"
        api_key = os.getenv("MAILGUN_API_KEY")

        print('api key', api_key)
        
        FROM_EMAIL_ADDRESS = "John Doe <mercury.spec77@gmail.com>"

        resp = requests.post(MAILGUN_API_URL, auth=("api", api_key),
            data={"from": FROM_EMAIL_ADDRESS,
            "to": to_mail, "subject": "Email verification", "text": f"{content}"})
        return resp

    except Exception as ex:
        print(f"Mailgun error: {ex}")

    # url = "https://api.postmarkapp.com/email"
    # server_token = os.getenv("MAILGUN_KEY")

    # # Define the email data
    # email_data = {
    #     "From": os.getenv("MAILGUN_REGISTERED_EMAIL"),
    #     "To": to_mail,
    #     "Subject": "Email Verification",
    #     "TextBody": "Hey registering user.",
    #     "HtmlBody": f"{content}",
    #     "MessageStream": "outbound"
    # }

    # # Define headers
    # headers = {
    #     "Accept": "application/json",
    #     "Content-Type": "application/json",
    #     "X-Postmark-Server-Token": server_token,
    # }

    # response = requests.post(url, json=email_data, headers=headers)
    # return response


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny,]
    authentication_classes = ()

    # TODO: increase rate limit 
    # @ratelimit(key='ip', rate='5/min')
    def post(self, request):
        try:
            data = request.data
            firstName = data["first_name"]
            lastName = data["last_name"]
            role = data["user_type"]
            email = data["email"]
            password = data["password"]

            if password:
                if len(password) >= 6:
                    if not User.objects.filter(email=email).exists():
                        user = User.objects.create_user(
                            email=email,
                            full_name=firstName + " " + lastName,
                            first_name=firstName,
                            last_name=lastName,
                            user_type=role,
                            password=password,
                            email_verified=True,
                        )
                        if User.objects.filter(email=email).exists():
                            # mail verify
                            refresh = RefreshToken.for_user(user)
                            # response = send_mailgun_mail(
                            #     email,
                            #     f"{os.getenv('FRONT_URL')}/mail-verify/?token={str(refresh.access_token)}",
                            # )
                            response = send_mail(
                                email,
                                f"{os.getenv('FRONT_URL')}/mail-verify/?token={str(refresh.access_token)}",
                            )
                            print('response in send mail: ', response)
                            if response.status_code == 200:
                                return Response(
                                    {
                                        "success": "User created successfully and sent verification link."
                                    },
                                    status=status.HTTP_201_CREATED,
                                )
                            else:
                                return Response(
                                    {"success": "Resend verification link."},
                                    status=status.HTTP_201_CREATED,
                                )
                        else:
                            return Response(
                                {"error": "Something went wrong creating user"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )
                    else:
                        return Response(
                            {"error": "Username already exists"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        {"error": "Password must be at least 6 characters long"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"error": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            print(e)
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MailVerifyView(APIView):
    def post(self, request):
        user = request.user
        user.email_verified = True
        user.save()
        return Response({"success": "Email verified"}, status=status.HTTP_200_OK)


class ForgetPasswordView(APIView):
    permission_classes = [AllowAny,]
    authentication_classes = ()

    def post(self, request):
        email = request.data["email"]
        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            response = send_mail(
                email,
                f"{os.getenv('FRONT_URL')}/reset-password/?token={str(refresh.access_token)}",
            )
            if response.status_code == 200:
                return Response(
                    {"success": "sent verification link."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"success": "Resend verification link."},
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            print(e)
            return Response(
                {"error": "user does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )


class ResetPasswordView(APIView):
    def post(self, request):
        user = request.user
        password = request.data["password"]
        confirm_password = request.data["confirmPassword"]
        if password == confirm_password:
            user.password = password
            user.save()
            return Response({"success": "reset password"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "password not matched"})


class LoginView(APIView):
    permission_classes = [AllowAny,]
    authentication_classes = ()

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            user = authenticate(request, email=email, password=password)
            userSerializer = UserSerializer(user)
            if user is not None:
                if user.email_verified:
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    return Response(
                        {
                            "status": {
                                "type": "success",
                                "message": "Welcome back! You have successfully logged in.",
                            },
                            "result": {
                                "token": str(refresh.access_token),
                                "user": userSerializer.data,
                            },
                            "navigate": "/home",
                        },
                    )
                else:
                    return Response(
                        {
                            "error": "Email not verified",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                return Response(
                    {
                        "error": "Invalid email or password",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.error_messages)


class GetUserView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user

        return Response(
            {
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

class GetUserInfo(APIView):
    def post(self, request):
        # Retrieve all users from the database
        all_users = User.objects.all()

        # Extract relevant information (username and email) from each user object
        users_info = [
            {"username": user.full_name, "email": user.email} for user in all_users
        ]

        return Response({"user": users_info}, status=status.HTTP_200_OK)


class loginWithGoogle(APIView):
    permission_classes = [AllowAny,]
    authentication_classes = ()

    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")

        # Check if the user already exists
        user, created = User.objects.get_or_create(full_name=name, email=email)
        if created:
            user.full_name = name
            user.mail_verify = True
            user.save()

        return Response("User saved successfully", status=status.HTTP_200_OK)
    
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        try:
            data = request.data
            user = request.user

            # Update user profile fields if they are not blank
            if 'phone_number' in data and data['phone_number']:
                user.phone_number = data['phone_number']
            if 'address' in data and data['address']:
                user.address = data['address']
            if 'years_of_experience' in data and data['years_of_experience'] is not None:
                user.years_of_experience = data['years_of_experience']
            if 'specialization' in data and data['specialization']:
                user.specialization = data['specialization']
            if 'first_name' in data and data['first_name']:
                user.first_name = data['first_name']
            if 'last_name' in data and data['last_name']:
                user.last_name = data['last_name']

            # Handle qualifications
            qualifications = data.get('qualifications', [])
            existing_qualifications = {f"{q['name']} ({q['year']})" for q in qualifications}

            current_qualifications = {f"{q.name} ({q.year})" for q in user.qualifications.all()}

            # Add new qualifications that are not already present
            for qualification in qualifications:
                name = qualification.get('name')
                year = qualification.get('year')

                if name and year:
                    qualification_str = f"{name} ({year})"
                    if qualification_str not in current_qualifications:
                        Qualification.objects.get_or_create(name=name, year=year)
                        user.qualifications.add(Qualification.objects.get(name=name, year=year))
            avatar_image_base64 = data.get('avatar_image')
            if avatar_image_base64:
                # Decode the Base64 string
                format, imgstr = avatar_image_base64.split(';base64,')  # Split format and data
                ext = format.split('/')[-1]  # Extract the image file extension (e.g., jpg, png)
                file_name = f"{user.id}_avatar.{ext}"
                file_path = os.path.join(settings.MEDIA_ROOT, 'avatar_images', file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists

                # Save the file
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(imgstr))

                # Save the relative path to the user's profile
                user.avatar_image = f"avatar_images/{file_name}"

            # Handle Base64-encoded banner image
            banner_image_base64 = data.get('banner_image')
            if banner_image_base64:
                # Decode the Base64 string
                format, imgstr = banner_image_base64.split(';base64,')  # Split format and data
                ext = format.split('/')[-1]  # Extract the image file extension
                file_name = f"{user.id}_banner.{ext}"
                file_path = os.path.join(settings.MEDIA_ROOT, 'banner_images', file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists

                # Save the file
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(imgstr))

                # Save the relative path to the user's profile
                user.banner_image = f"banner_images/{file_name}"

            user.save()

            userSerializer = UserSerializer(user)
            return Response(
                {
                    "status": {
                        "type": "success",
                        "message": "Profile Updated successfully.",
                    },
                    "result": {
                        "user": userSerializer.data,
                    },
                    "navigate": "/home",
                },
            )

        except Exception as e:
            return Response({"error": str(e)}, status=400)

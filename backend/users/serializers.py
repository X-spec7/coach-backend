from rest_framework import serializers

from backend.users.models import User, CoachProfile

from django.conf import settings


class ClientSerializer(serializers.ModelSerializer):
    avatarImageUrl = serializers.SerializerMethodField()

    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    fullName = serializers.CharField(source='full_name')
    phoneNumber = serializers.CharField(source='phone_number')
    userType = serializers.CharField(source='user_type')
    isSuperuser = serializers.BooleanField(source='is_superuser')

    class Meta:
        model = User
        fields = [
            'id',
            'firstName',
            'lastName',
            'userType',
            'email',
            'address',
            'isSuperuser',
            'phoneNumber',
            'avatarImageUrl',
        ]

    def get_avatarImageUrl(self, obj):
        if obj.avatar_image:
            return f"{settings.MEDIA_URL}{obj.avatar_image}"
        return None

class CoachSerializer(ClientSerializer):
    bannerImageUrl = serializers.SerializerMethodField()
    yearsOfExperience = serializers.SerializerMethodField()
    specialization = serializers.SerializerMethodField()
    certifications = serializers.SerializerMethodField()

    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + [
            'bannerImageUrl',
            'yearsOfExperience',
            'specialization',
            'certifications',
        ]
    
    def get_bannerImageUrl(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        if coach_profile.banner_image:
            return f"{settings.MEDIA_URL}{coach_profile.banner_image}"
    def get_yearsOfExperience(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        return coach_profile.years_of_experience
    def get_specialization(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        return coach_profile.specialization
    def get_certifications(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        certifications = coach_profile.certifications.all()

        return [
            {
                "certificationTitle": cert.certification_title,
                "certificationDetail": cert.certification_detail
            }
            for cert in certifications
        ]

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
class GetCoachesRequestDTO(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, required=True)
    offset = serializers.IntegerField(min_value=0, required=True)
    query = serializers.CharField(max_length=20)
    specialization = serializers.CharField(max_length=20, default="All")
    listedState = serializers.CharField(max_length=20, default="All")

class GetCoachesTotalCountRequestDTO(serializers.Serializer):
    query = serializers.CharField(max_length=20)
    specialization = serializers.CharField(max_length=20, default="All")
    listedState = serializers.CharField(max_length=20, default="All")

class GetCoachByIdRequestDTO(serializers.Serializer):
    coachId = serializers.IntegerField(required=True)

class GetCoachesResponseDTO(serializers.Serializer):
    coachBannerImageUrl = serializers.SerializerMethodField()
    coachName = serializers.CharField(source='full_name')
    specialization = serializers.SerializerMethodField()
    listed = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'coachBannerImageUrl',
            'coachName',
            'specialization',
            'listed',
        ]
    
    def get_coachBannerImageUrl(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        if coach_profile.banner_image:
            return f"{settings.MEDIA_URL}{coach_profile.banner_image}"
    def get_specialization(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        return coach_profile.specialization
    def listed(self, obj):
        coach_profile = CoachProfile.objects.get(user=obj)
        return coach_profile.listed
    
class GetCoachByIdResponseDTO(CoachSerializer):
    # members = serializers.SerializerMethodField()
    # classes = serializers.SerializerMethodField()
    # reviews = serializers.SerializerMethodField()

    class Meta(CoachSerializer.Meta):
        fields = CoachSerializer.Meta.fields + [
            # 'members',
            # 'classes',
            # 'reviews',
        ]

# class CoachDetailSerializer(serializers.Serializer):

#     class Meta:
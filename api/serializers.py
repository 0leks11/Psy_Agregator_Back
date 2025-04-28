from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    UserProfile, TherapistProfile, ClientProfile, InviteCode, Role, Gender,
    Skill, Language, TherapistPhoto, Publication
)
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import uuid
from django.conf import settings

User = get_user_model()

DEFAULT_AVATAR_URL = settings.MEDIA_URL + 'defaults/default-avatar.png'

# --- Сериализаторы для Списков Выбора ---
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'description')

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'name', 'code')

# --- Сериализаторы для Отображения Профилей ---
class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='get_role_display', read_only=True)
    gender = serializers.CharField(source='get_gender_display', read_only=True)
    gender_code = serializers.CharField(source='gender', write_only=True, required=False, allow_blank=True)
    profile_picture_url = serializers.SerializerMethodField()
    pronouns = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ('role', 'gender', 'gender_code', 'pronouns', 'profile_picture_url')

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        if request:
            return request.build_absolute_uri(DEFAULT_AVATAR_URL)
        return DEFAULT_AVATAR_URL

class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')

# --- Сериализатор для фотографий психолога ---
class TherapistPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TherapistPhoto
        fields = ('id', 'image', 'image_url', 'caption', 'order', 'therapist_profile')
        read_only_fields = ('therapist_profile',)
        
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class TherapistProfileReadSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer(read_only=True)
    profile = UserProfileSerializer(source='user.profile', read_only=True)
    skills = serializers.StringRelatedField(many=True, read_only=True)
    languages = serializers.StringRelatedField(many=True, read_only=True)
    total_hours_worked = serializers.SerializerMethodField()
    photos = TherapistPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = TherapistProfile
        fields = (
            'id', 'user', 'profile', 'about', 'experience_years',
            'is_verified', 'is_subscribed',
            'skills', 'languages',
            'total_hours_worked',
            'office_location',
            'video_intro_url', 'website_url', 'linkedin_url',
            'photos',
        )

    def get_total_hours_worked(self, obj):
        if obj.display_hours and obj.total_hours_worked is not None:
            return obj.total_hours_worked
        return None

class ClientProfileReadSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer(read_only=True)
    profile = UserProfileSerializer(source='user.profile', read_only=True)
    interested_topics = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = ClientProfile
        fields = ('id', 'user', 'profile', 'interested_topics', 'request_details')

# --- Сериализаторы для Текущего Пользователя ---
class CurrentUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    therapist_profile = serializers.SerializerMethodField()
    client_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'profile', 'therapist_profile', 'client_profile')
        read_only_fields = fields

    def get_therapist_profile(self, obj):
        if hasattr(obj, 'therapist_profile'):
            return TherapistProfileDetailedSerializer(obj.therapist_profile).data
        return None

    def get_client_profile(self, obj):
        if hasattr(obj, 'client_profile'):
            return ClientProfileDetailedSerializer(obj.client_profile).data
        return None

class TherapistProfileDetailedSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True, required=False)
    languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, required=False)

    class Meta:
        model = TherapistProfile
        fields = ('about', 'experience_years', 'skills', 'languages',
                  'total_hours_worked', 'display_hours', 'office_location',
                  'is_verified', 'is_subscribed',
                  'short_video_url', 'status', 'photos')

class ClientProfileDetailedSerializer(serializers.ModelSerializer):
    interested_topics = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True, required=False)

    class Meta:
        model = ClientProfile
        fields = ('request_details', 'interested_topics')

# --- Сериализаторы для Обновления Профилей ---
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    gender = serializers.ChoiceField(choices=Gender.choices, required=False)

    class Meta:
        model = UserProfile
        fields = ('gender',)

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class TherapistProfileUpdateSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True, required=False)
    languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, required=False)
    total_hours_worked = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    class Meta:
        model = TherapistProfile
        fields = ('about', 'experience_years', 'skills', 'languages',
                  'total_hours_worked', 'display_hours', 'office_location',
                  'short_video_url', 'website_url', 'linkedin_url')

class ClientProfileUpdateSerializer(serializers.ModelSerializer):
    interested_topics = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True, required=False)

    class Meta:
        model = ClientProfile
        fields = ('request_details', 'interested_topics')

# --- Сериализаторы для Регистрации ---
class ClientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {'username': {'required': False}}

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data['public_id'] = uuid.uuid4()
        validated_data.pop('password_confirm')
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email']
            
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_client=True
        )
        
        UserProfile.objects.create(user=user, role=Role.CLIENT)
        ClientProfile.objects.create(user=user)
        print(f"Client registered: {user.email}, UserProfile and ClientProfile created.")
        return user

class TherapistRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    invite_code = serializers.CharField()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirm', 'invite_code', 'first_name', 'last_name')
        extra_kwargs = {'username': {'required': False}}

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def validate_invite_code(self, value):
        try:
            invite_code = InviteCode.objects.get(code=value, is_used=False)
        except InviteCode.DoesNotExist:
            raise serializers.ValidationError("Недействительный или уже использованный код приглашения")
        return invite_code

    @transaction.atomic
    def create(self, validated_data):
        validated_data['public_id'] = uuid.uuid4()
        invite_code_obj = validated_data.pop('invite_code')
        validated_data.pop('password_confirm')
        
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email']
            
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_therapist=True
        )
        
        UserProfile.objects.create(user=user, role=Role.THERAPIST)
        TherapistProfile.objects.create(user=user)
        
        invite_code_obj.is_used = True
        invite_code_obj.save()
        print(f"Therapist registered: {user.email}, UserProfile and TherapistProfile created.")
        return user

class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")
    password = serializers.CharField(
        label="Password",
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    attrs['user'] = user
                    return attrs
            except User.DoesNotExist:
                pass
            
            msg = 'Не удается войти с предоставленными учетными данными.'
            raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Должны быть указаны "email" и "password".'
            raise serializers.ValidationError(msg, code='authorization')

class TherapistProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistProfile
        fields = ['about', 'experience_years', 'is_verified', 'is_subscribed', 'skills', 'languages',
                 'short_video_url', 'website_url', 'linkedin_url']

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['request_details', 'interested_topics']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    therapist_profile = TherapistProfileSerializer(read_only=True)
    client_profile = ClientProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'profile', 'therapist_profile', 'client_profile']

class InviteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteCode
        fields = ['code', 'is_used', 'created_at']

# --- Сериализаторы для публикаций ---
class PublicationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения публикаций
    """
    author_name = serializers.SerializerMethodField()
    author_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Publication
        fields = (
            'id', 'author', 'author_name', 'author_photo',
            'title', 'content', 'created_at', 'updated_at'
        )
        read_only_fields = ('author', 'created_at', 'updated_at')
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"
    
    def get_author_photo(self, obj):
        if hasattr(obj.author, 'profile') and obj.author.profile.profile_picture:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.author.profile.profile_picture.url)
            return obj.author.profile.profile_picture.url
        return None

class PublicationWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления публикаций
    """
    class Meta:
        model = Publication
        fields = ('title', 'content')
        
    def create(self, validated_data):
        # author устанавливается в представлении
        return Publication.objects.create(**validated_data)

class SimplePublicationSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения публикации"""
    class Meta:
        model = Publication
        fields = ('id', 'title', 'created_at')
        read_only_fields = fields

class PublicUserProfileSerializer(serializers.ModelSerializer):
    # --- Поля из User ---
    public_id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)

    # --- Поля из UserProfile ---
    pronouns = serializers.CharField(source='profile.pronouns', read_only=True, allow_null=True)
    profile_picture_url = serializers.SerializerMethodField()

    # --- Поля из TherapistProfile ---
    about = serializers.CharField(source='therapist_profile.about', read_only=True, allow_null=True)
    skills = SkillSerializer(source='therapist_profile.skills', many=True, read_only=True)
    languages = LanguageSerializer(source='therapist_profile.languages', many=True, read_only=True)
    short_video_url = serializers.URLField(source='therapist_profile.short_video_url', read_only=True, allow_null=True)
    status = serializers.CharField(source='therapist_profile.status', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='therapist_profile.get_status_display', read_only=True)
    photos = serializers.JSONField(source='therapist_profile.photos', read_only=True)

    # --- Поля из Publication ---
    publications = SimplePublicationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'public_id', 'first_name', 'last_name', 'pronouns', 'profile_picture_url',
            'about', 'skills', 'languages', 'short_video_url', 'status', 'status_display',
            'publications', 'photos'
        )
        read_only_fields = fields

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        # Проверяем наличие profile и картинки в нем
        if hasattr(obj, 'profile') and obj.profile and obj.profile.profile_picture and hasattr(obj.profile.profile_picture, 'url'):
            if request:
                return request.build_absolute_uri(obj.profile.profile_picture.url)
            return obj.profile.profile_picture.url
        # Иначе возвращаем дефолтный аватар
        if request:
            return request.build_absolute_uri(DEFAULT_AVATAR_URL)
        return DEFAULT_AVATAR_URL

class TherapistCardSerializer(serializers.ModelSerializer):
    """Сериализатор для данных, необходимых в TherapistCard на фронтенде"""
    public_id = serializers.UUIDField(read_only=True)
    profile = serializers.SerializerMethodField()
    therapist_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'public_id', 'first_name', 'last_name', 'profile', 'therapist_profile')

    def get_profile(self, obj):
        request = self.context.get('request')
        picture_url = DEFAULT_AVATAR_URL  # Дефолтное значение
        if hasattr(obj, 'profile') and obj.profile and obj.profile.profile_picture and hasattr(obj.profile.profile_picture, 'url'):
            picture_url = obj.profile.profile_picture.url  # URL своей картинки

        # Строим абсолютный URL, если есть request
        absolute_picture_url = request.build_absolute_uri(picture_url) if request else picture_url
        return {
            'profile_picture_url': absolute_picture_url
        }

    def get_therapist_profile(self, obj):
        if hasattr(obj, 'therapist_profile') and obj.therapist_profile:
            tp = obj.therapist_profile
            skills_data = SkillSerializer(tp.skills.all()[:3], many=True).data
            return {
                'about': (tp.about[:100] + '...') if tp.about and len(tp.about) > 100 else tp.about,
                'experience_years': tp.experience_years,
                'is_verified': tp.is_verified,
                'status': tp.status,
                'status_display': tp.get_status_display(),
                'skills': skills_data,
                'skills_count': tp.skills.count()
            }
        return None 
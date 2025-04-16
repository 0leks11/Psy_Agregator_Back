from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    UserProfile, TherapistProfile, ClientProfile, InviteCode, Role, Gender,
    Skill, Language
)
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

User = get_user_model()

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
    profile_picture_url = serializers.ImageField(source='profile_picture', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('role', 'gender', 'gender_code', 'profile_picture_url')

class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')

class TherapistProfileReadSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer(read_only=True)
    profile = UserProfileSerializer(source='user.profile', read_only=True)
    skills = serializers.StringRelatedField(many=True, read_only=True)
    languages = serializers.StringRelatedField(many=True, read_only=True)
    total_hours_worked = serializers.SerializerMethodField()

    class Meta:
        model = TherapistProfile
        fields = (
            'id', 'user', 'profile', 'about', 'experience_years',
            'is_verified', 'is_subscribed',
            'skills', 'languages',
            'total_hours_worked',
            'office_location',
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
                  'is_verified', 'is_subscribed')

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
                  'total_hours_worked', 'display_hours', 'office_location')

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
        fields = ['about', 'experience_years', 'is_verified', 'is_subscribed', 'skills', 'languages']

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
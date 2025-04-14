from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, TherapistProfile, ClientProfile, InviteCode
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db import transaction

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_therapist', 'is_client')
        read_only_fields = ('id',)

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class TherapistProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TherapistProfile
        fields = ('id', 'user', 'bio', 'experience_years', 'profile_picture', 
                 'is_verified', 'is_subscribed', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ClientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ClientProfile
        fields = ('id', 'user', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class InviteCodeSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = InviteCode
        fields = ('id', 'code', 'is_used', 'created_by', 'created_at', 'used_at')
        read_only_fields = ('id', 'created_at', 'used_at')

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
        
        # Создаем UserProfile с именем из first_name и last_name
        name = f"{validated_data.get('first_name', '')} {validated_data.get('last_name', '')}".strip()
        UserProfile.objects.create(user=user, name=name)
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
        
        # Создаем UserProfile с именем из first_name и last_name
        name = f"{validated_data.get('first_name', '')} {validated_data.get('last_name', '')}".strip()
        UserProfile.objects.create(user=user, name=name)
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
            # Пытаемся найти пользователя по email
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    # Если пароль верный, сохраняем пользователя в attrs
                    attrs['user'] = user
                    return attrs
            except User.DoesNotExist:
                pass
            
            # Если не нашли пользователя или пароль неверный
            msg = 'Не удается войти с предоставленными учетными данными.'
            raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Должны быть указаны "email" и "password".'
            raise serializers.ValidationError(msg, code='authorization') 
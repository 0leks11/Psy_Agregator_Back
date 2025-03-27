from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, TherapistProfile, ClientProfile, InviteCode

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
    user_profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'user_profile')

    def create(self, validated_data):
        profile_data = validated_data.pop('user_profile')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            is_client=True
        )
        UserProfile.objects.create(user=user, **profile_data)
        ClientProfile.objects.create(user=user)
        return user

class TherapistRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_profile = UserProfileSerializer()
    invite_code = serializers.CharField()

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'user_profile', 'invite_code')

    def validate_invite_code(self, value):
        try:
            invite_code = InviteCode.objects.get(code=value, is_used=False)
        except InviteCode.DoesNotExist:
            raise serializers.ValidationError("Недействительный или уже использованный код приглашения")
        return invite_code

    def create(self, validated_data):
        profile_data = validated_data.pop('user_profile')
        invite_code = validated_data.pop('invite_code')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            is_therapist=True
        )
        
        UserProfile.objects.create(user=user, **profile_data)
        TherapistProfile.objects.create(user=user)
        
        invite_code.is_used = True
        invite_code.save()
        
        return user 
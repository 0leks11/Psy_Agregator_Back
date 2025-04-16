from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# --- Новые модели для выбора ---
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Role(models.TextChoices):
    CLIENT = 'CLIENT', 'Client'
    THERAPIST = 'THERAPIST', 'Therapist'
    ADMIN = 'ADMIN', 'Admin'

class Gender(models.TextChoices):
    MALE = 'MALE', 'Мужчина'
    FEMALE = 'FEMALE', 'Женщина'
    OTHER = 'OTHER', 'Другое'
    PREFER_NOT_TO_SAY = 'UNKNOWN', 'Не указан'

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_therapist = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()}"

class TherapistProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_profile')
    about = models.TextField("О себе", blank=True, null=True)
    experience_years = models.PositiveIntegerField("Лет опыта", default=0)
    is_verified = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False)
    skills = models.ManyToManyField(Skill, blank=True, related_name='therapists', verbose_name="Навыки/Специализации")
    languages = models.ManyToManyField(Language, blank=True, related_name='therapists', verbose_name="Языки")
    total_hours_worked = models.PositiveIntegerField("Всего часов практики", blank=True, null=True)
    display_hours = models.BooleanField("Показывать часы практики в профиле", default=False)
    office_location = models.CharField("Место/Формат работы", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Therapist: {self.user.email}"

class ClientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_profile')
    request_details = models.TextField("Описание запроса", blank=True, null=True)
    interested_topics = models.ManyToManyField(Skill, blank=True, related_name='interested_clients', verbose_name="Интересующие темы/запросы")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Client: {self.user.email}"

class InviteCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_invite_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invite code: {self.code}"

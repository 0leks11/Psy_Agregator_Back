from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import UserProfile, TherapistProfile, ClientProfile, InviteCode

User = get_user_model()

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class TherapistProfileInline(admin.StackedInline):
    model = TherapistProfile
    can_delete = False

class ClientProfileInline(admin.StackedInline):
    model = ClientProfile
    can_delete = False

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_therapist', 'is_client', 'is_staff')
    list_filter = ('is_therapist', 'is_client', 'is_staff')
    search_fields = ('email', 'username')
    inlines = [UserProfileInline]

    def get_inlines(self, request, obj=None):
        if obj and obj.is_therapist:
            return [UserProfileInline, TherapistProfileInline]
        elif obj and obj.is_client:
            return [UserProfileInline, ClientProfileInline]
        return [UserProfileInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    search_fields = ('user__email', 'name')

@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'is_subscribed', 'experience_years')
    list_filter = ('is_verified', 'is_subscribed')
    search_fields = ('user__email', 'bio')

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__email',)

@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_used', 'created_by', 'created_at', 'used_at')
    list_filter = ('is_used',)
    search_fields = ('code', 'created_by__email')

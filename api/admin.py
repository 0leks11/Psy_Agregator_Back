from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, UserProfile, TherapistProfile, ClientProfile, InviteCode,
    Skill, Language
)

# --- Регистрация новых моделей ---
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

# --- Обновление существующих админок ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'gender', 'profile_picture', 'display_profile_picture')
    readonly_fields = ('display_profile_picture',)

    def display_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', obj.profile_picture.url)
        return "Нет фото"
    display_profile_picture.short_description = 'Текущее фото'

class TherapistProfileInline(admin.StackedInline):
    model = TherapistProfile
    can_delete = False
    verbose_name_plural = 'Therapist Profile'
    fields = ('about', 'experience_years', 'skills', 'languages', 'total_hours_worked', 'display_hours', 'office_location', 'is_verified', 'is_subscribed')
    filter_horizontal = ('skills', 'languages',)

class ClientProfileInline(admin.StackedInline):
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Client Profile'
    fields = ('request_details', 'interested_topics')
    filter_horizontal = ('interested_topics',)

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, TherapistProfileInline, ClientProfileInline)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'get_role', 'get_verification_status')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    @admin.display(description='Role')
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except: return 'N/A'

    @admin.display(description='Verified (Therapist)')
    def get_verification_status(self, obj):
        if hasattr(obj, 'therapist_profile'):
            return obj.therapist_profile.is_verified
        return 'N/A'

# Перерегистрация User с новой админкой
if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, UserAdmin)

@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'is_subscribed', 'experience_years', 'display_hours')
    list_filter = ('is_verified', 'is_subscribed', 'display_hours', 'languages', 'skills')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'about')
    list_editable = ('is_verified', 'is_subscribed', 'display_hours')
    raw_id_fields = ('user',)
    filter_horizontal = ('skills', 'languages',)

@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_used', 'created_by', 'created_at', 'used_at')
    list_filter = ('is_used',)
    search_fields = ('code', 'created_by__email')

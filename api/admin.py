from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, UserProfile, TherapistProfile, ClientProfile, InviteCode,
    Skill, Language, TherapistPhoto, Publication
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

# Inline для фото в профиле терапевта
class TherapistPhotoInline(admin.TabularInline):  # Используем Tabular для компактности
    model = TherapistPhoto
    extra = 1  # Показывать одно поле для добавления нового фото
    fields = ('image', 'display_image', 'caption', 'order')
    readonly_fields = ('display_image',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "Нет фото"
    display_image.short_description = 'Превью'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'gender', 'profile_picture_preview')
    list_filter = ('role', 'gender')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" height="50" />', obj.profile_picture.url)
        return "Нет фото"
    profile_picture_preview.short_description = 'Фото профиля'

@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'is_subscribed', 'experience_years', 'display_hours', 'status')
    list_filter = ('is_verified', 'is_subscribed', 'display_hours', 'status', 'languages', 'skills')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'about')
    list_editable = ('is_verified', 'is_subscribed', 'display_hours')
    raw_id_fields = ('user',)
    filter_horizontal = ('skills', 'languages',)
    inlines = [TherapistPhotoInline]

    fields = (
        'user',
        'about',
        'experience_years',
        'skills',
        'languages',
        'total_hours_worked',
        'display_hours',
        'office_location',
        'status',
        'short_video_url',
        'photos',
        'is_verified',
        'is_subscribed'
    )

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'request_details')
    raw_id_fields = ('user',)
    filter_horizontal = ('interested_topics',)

@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_used', 'created_by', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('code', 'created_by__email')
    readonly_fields = ('created_at',)

# Админка для Публикаций
@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_email', 'created_at', 'updated_at')
    list_filter = ('author',)
    search_fields = ('title', 'content', 'author__email')
    raw_id_fields = ('author',)
    readonly_fields = ('created_at', 'updated_at')
    fields = ('author', 'title', 'content', 'created_at', 'updated_at')

    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Автор'
    author_email.admin_order_field = 'author__email'

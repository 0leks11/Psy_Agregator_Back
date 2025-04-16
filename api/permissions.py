from rest_framework import permissions
from .models import Role

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только владельцам объекта редактировать его.
    Запросы GET, HEAD и OPTIONS разрешены для любого пользователя.
    Только владелец может выполнять запросы POST, PUT, PATCH, DELETE.
    """
    
    def has_permission(self, request, view):
        # Любой аутентифицированный пользователь может читать
        # Неаутентифицированные пользователи могут только читать
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для небезопасных методов нужна аутентификация
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Запросы READ разрешены для любого запроса
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Проверка авторства объекта (должно быть поле author у объекта)
        if hasattr(obj, 'author'):
            return obj.author == request.user
        
        # Проверка владельца объекта (user поле)
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # По умолчанию запрещаем
        return False


class IsTherapistOwner(permissions.BasePermission):
    """
    Разрешение только для терапистов, которые являются владельцами профиля.
    Это разрешение используется для ресурсов, принадлежащих конкретному
    профилю терапевта (например, его фотографии).
    """
    
    def has_permission(self, request, view):
        # Проверяем, что пользователь аутентифицирован
        if not request.user.is_authenticated:
            return False
            
        # Проверяем, что у пользователя есть профиль терапевта
        return hasattr(request.user, 'therapist_profile')
    
    def has_object_permission(self, request, view, obj):
        # Проверяем, что пользователь аутентифицирован
        if not request.user.is_authenticated:
            return False
            
        # Проверяем, что у пользователя есть профиль терапевта
        if not hasattr(request.user, 'therapist_profile'):
            return False
            
        # Проверяем, что объект принадлежит профилю терапевта пользователя
        # Для TherapistPhoto с полем therapist_profile
        if hasattr(obj, 'therapist_profile'):
            return obj.therapist_profile == request.user.therapist_profile
            
        return False 
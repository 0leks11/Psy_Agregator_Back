from django.core.management.base import BaseCommand
from api.models import InviteCode, User
import secrets

class Command(BaseCommand):
    help = 'Создает новый код приглашения для регистрации терапевтов'

    def handle(self, *args, **options):
        # Получаем или создаем суперпользователя
        superuser, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'is_therapist': True
            }
        )
        
        # Генерируем случайный код
        code = secrets.token_urlsafe(8)
        
        # Создаем код приглашения
        invite_code = InviteCode.objects.create(
            code=code,
            created_by=superuser
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Создан код приглашения: {code}')
        ) 
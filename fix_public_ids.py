import os
import django
import uuid

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import User

def fix_null_public_ids():
    users_to_fix = User.objects.filter(public_id__isnull=True)
    if users_to_fix.exists():
        print(f"Found {users_to_fix.count()} users with null public_id. Fixing...")
        for user in users_to_fix:
            user.public_id = uuid.uuid4()
            user.save(update_fields=['public_id'])
            print(f"Updated public_id for user ID {user.id}")
        print("Fix complete.")
    else:
        print("No users with null public_id found.")

if __name__ == "__main__":
    fix_null_public_ids() 
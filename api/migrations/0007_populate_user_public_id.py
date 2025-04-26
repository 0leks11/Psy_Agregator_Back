import uuid
from django.db import migrations

def populate_public_id(apps, schema_editor):
    User = apps.get_model('api', 'User')
    for user in User.objects.filter(public_id__isnull=True):
        user.public_id = uuid.uuid4()
        user.save(update_fields=['public_id'])

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0006_alter_publication_id'),
    ]

    operations = [
        migrations.RunPython(populate_public_id),
    ] 
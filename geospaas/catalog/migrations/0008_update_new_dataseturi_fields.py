from urllib.parse import urlparse

from django.db import migrations

from geospaas.catalog.managers import DAP_SERVICE_NAME, OPENDAP_SERVICE 

def set_service(apps, schema_editor):
    model = apps.get_model('catalog', 'dataseturi')
    for row in model.objects.all():
        if 'http' in urlparse(row.uri).scheme:
            row.name = DAP_SERVICE_NAME
            row.service = OPENDAP_SERVICE
            row.save(update_fields=['name', 'service'])

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_auto_20190626_1313'),
    ]

    operations = [
        migrations.RunPython(set_service, reverse_code=migrations.RunPython.noop),
    ]

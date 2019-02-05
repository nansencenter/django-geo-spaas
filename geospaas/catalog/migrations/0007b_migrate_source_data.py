from django.db import migrations

def copy_source(apps, schema_editor):
    Dataset = apps.get_model('geospaas.catalog', 'Dataset')
    for ds in Dataset.objects.all():
        ds.sources.add(ds.source)

def copy_source_backwards(apps, schema_editor):
    Dataset = apps.get_model('geospaas.catalog', 'Dataset')
    for ds in Dataset.objects.all():
        ds.source = ds.sources.all()[0]

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007a_add_sources_field'),
    ]

    operations = [
            migrations.RunPython(copy_source, copy_source_backwards),
    ]

# Generated by Django 3.0 on 2020-05-07 08:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_auto_20200331_0806'),
        ('base_viewer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Search_with_para',
            fields=[
                ('search_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='base_viewer.Search')),
                ('DatasetParameter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.DatasetParameter')),
            ],
            bases=('base_viewer.search',),
        ),
    ]

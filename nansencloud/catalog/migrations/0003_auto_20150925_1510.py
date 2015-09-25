# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_auto_20150925_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datalocation',
            name='file',
            field=models.FileField(default=None, storage=django.core.files.storage.FileSystemStorage(location=b'/vagrant/shared/test_data'), null=True, upload_to=b''),
        ),
    ]

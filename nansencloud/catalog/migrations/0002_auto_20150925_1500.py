# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datalocation',
            name='dap',
            field=models.URLField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='datalocation',
            name='ftp',
            field=models.URLField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='datalocation',
            name='http',
            field=models.URLField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='datalocation',
            name='wfs',
            field=models.URLField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='datalocation',
            name='wms',
            field=models.URLField(default=None, null=True),
        ),
    ]

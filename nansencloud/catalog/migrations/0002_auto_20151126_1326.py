# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='source',
            old_name='sensor',
            new_name='instrument',
        ),
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('platform', 'instrument')]),
        ),
    ]

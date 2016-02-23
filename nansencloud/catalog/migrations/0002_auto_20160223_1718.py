# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visualization',
            name='parameters',
        ),
        migrations.RemoveField(
            model_name='visualizationparameter',
            name='ds_parameter',
        ),
        migrations.RemoveField(
            model_name='visualizationparameter',
            name='visualization',
        ),
        migrations.AlterField(
            model_name='parameter',
            name='gcmd_science_keyword',
            field=models.ForeignKey(blank=True, to='gcmd_keywords.ScienceKeyword', null=True),
        ),
        migrations.DeleteModel(
            name='Visualization',
        ),
        migrations.DeleteModel(
            name='VisualizationParameter',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_auto_20160223_1718'),
        ('viewer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Visualization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='VisualizationParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ds_parameter', models.ForeignKey(to='catalog.DatasetParameter')),
                ('visualization', models.ForeignKey(to='viewer.Visualization')),
            ],
        ),
        migrations.AddField(
            model_name='visualization',
            name='parameters',
            field=models.ManyToManyField(to='catalog.DatasetParameter', through='viewer.VisualizationParameter'),
        ),
    ]

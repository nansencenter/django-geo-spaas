# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Search',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sdate', models.DateTimeField(null=True, blank=True)),
                ('date0', models.DateField()),
                ('date1', models.DateField()),
                ('polygon', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('source', models.ForeignKey(blank=True, to='catalog.Source', null=True)),
            ],
        ),
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
        migrations.CreateModel(
            name='Dataset',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('catalog.dataset',),
        ),
        migrations.AddField(
            model_name='visualization',
            name='parameters',
            field=models.ManyToManyField(to='catalog.DatasetParameter', through='viewer.VisualizationParameter'),
        ),
    ]

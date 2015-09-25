# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(default=None, upload_to=b'')),
                ('dap', models.URLField(default=None)),
                ('ftp', models.URLField(default=None)),
                ('http', models.URLField(default=None)),
                ('wms', models.URLField(default=None)),
                ('wfs', models.URLField(default=None)),
            ],
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_coverage_start', models.DateTimeField()),
                ('time_coverage_end', models.DateTimeField()),
                ('data_location', models.ManyToManyField(to='catalog.DataLocation')),
            ],
        ),
        migrations.CreateModel(
            name='GeographicLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('type', models.CharField(max_length=15, choices=[(b'Grid', b'Grid'), (b'Point', b'Point'), (b'Trajectory', b'Trajectory')])),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=15, choices=[(b'Satellite', b'Satellite'), (b'In-situ', b'In-situ'), (b'Model', b'Model')])),
                ('platform', models.CharField(max_length=100)),
                ('tool', models.CharField(help_text=b'The tool could be instrument, model version, etc.', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=10)),
                ('standard_name', models.CharField(max_length=100)),
                ('long_name', models.CharField(max_length=200)),
                ('units', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='dataset',
            name='geolocation',
            field=models.OneToOneField(to='catalog.GeographicLocation'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='source',
            field=models.OneToOneField(to='catalog.Source'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='variables',
            field=models.ManyToManyField(to='catalog.Variable'),
        ),
    ]

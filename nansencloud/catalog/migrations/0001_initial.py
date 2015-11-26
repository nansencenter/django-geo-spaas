# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gcmd_keywords', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('protocol', models.CharField(max_length=15, choices=[(b'LOCALFILE', b'LOCALFILE'), (b'OPENDAP', b'OPENDAP'), (b'FTP', b'FTP'), (b'HTTP', b'HTTP'), (b'HTTPS', b'HTTPS'), (b'WMS', b'WMS'), (b'WFS', b'WFS')])),
                ('uri', models.URLField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_coverage_start', models.DateTimeField()),
                ('time_coverage_end', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='DatasetRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('child', models.ForeignKey(related_name='parents', to='catalog.Dataset')),
                ('parent', models.ForeignKey(related_name='children', to='catalog.Dataset')),
            ],
        ),
        migrations.CreateModel(
            name='GeographicLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=10)),
                ('standard_name', models.CharField(max_length=100)),
                ('long_name', models.CharField(max_length=200)),
                ('units', models.CharField(max_length=10)),
                ('time', models.DateTimeField()),
                ('location', models.ForeignKey(to='catalog.DataLocation')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('specs', models.CharField(default=b'', help_text=b'Further specifications of the source.', max_length=50)),
                ('platform', models.ForeignKey(to='gcmd_keywords.Platform')),
                ('sensor', models.ForeignKey(to='gcmd_keywords.Instrument')),
            ],
        ),
        migrations.AddField(
            model_name='dataset',
            name='geolocation',
            field=models.ForeignKey(to='catalog.GeographicLocation'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='source',
            field=models.ForeignKey(to='catalog.Source'),
        ),
        migrations.AddField(
            model_name='datalocation',
            name='dataset',
            field=models.ForeignKey(to='catalog.Dataset'),
        ),
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('platform', 'sensor')]),
        ),
    ]

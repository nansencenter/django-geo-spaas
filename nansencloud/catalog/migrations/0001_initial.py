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
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entry_title', models.CharField(max_length=220)),
                ('summary', models.TextField()),
                ('time_coverage_start', models.DateTimeField(null=True, blank=True)),
                ('time_coverage_end', models.DateTimeField(null=True, blank=True)),
                ('access_constraints', models.CharField(blank=True, max_length=50, null=True, choices=[(b'accessLevel0', 'Limited'), (b'accessLevel1', 'In-house'), (b'accessLevel2', 'Public')])),
                ('ISO_topic_category', models.ForeignKey(to='gcmd_keywords.ISOTopicCategory')),
                ('data_center', models.ForeignKey(to='gcmd_keywords.DataCenter')),
                ('gcmd_location', models.ForeignKey(blank=True, to='gcmd_keywords.Location', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DatasetParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset', models.ForeignKey(to='catalog.Dataset')),
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
            name='DatasetURI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.URLField(unique=True)),
                ('dataset', models.ForeignKey(to='catalog.Dataset')),
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
            name='Parameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('standard_name', models.CharField(max_length=300)),
                ('short_name', models.CharField(max_length=30)),
                ('units', models.CharField(max_length=10)),
                ('gcmd_science_keyword', models.ForeignKey(to='gcmd_keywords.ScienceKeyword')),
            ],
        ),
        migrations.CreateModel(
            name='Personnel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone', models.CharField(max_length=80)),
                ('fax', models.CharField(max_length=80)),
                ('address', models.CharField(max_length=80)),
                ('city', models.CharField(max_length=80)),
                ('province_or_state', models.CharField(max_length=80)),
                ('postal_code', models.CharField(max_length=80)),
                ('country', models.CharField(max_length=80)),
            ],
            options={
                'permissions': (('accessLevel0', 'Can access all data'), ('accessLevel1', 'Can access data at own data center'), ('accessLevel2', 'Can access public data only')),
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=20, choices=[(b'Investigator', b'Investigator'), (b'Technical Contact', b'Technical Contact'), (b'DIF Author', b'DIF Author')])),
                ('personnel', models.ForeignKey(to='catalog.Personnel')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('specs', models.CharField(default=b'', help_text='Further specifications of the source.', max_length=50)),
                ('instrument', models.ForeignKey(to='gcmd_keywords.Instrument')),
                ('platform', models.ForeignKey(to='gcmd_keywords.Platform')),
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
                ('visualization', models.ForeignKey(to='catalog.Visualization')),
            ],
        ),
        migrations.AddField(
            model_name='visualization',
            name='parameters',
            field=models.ManyToManyField(to='catalog.DatasetParameter', through='catalog.VisualizationParameter'),
        ),
        migrations.AddField(
            model_name='datasetparameter',
            name='parameter',
            field=models.ForeignKey(to='catalog.Parameter'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='geographic_location',
            field=models.ForeignKey(blank=True, to='catalog.GeographicLocation', null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='parameters',
            field=models.ManyToManyField(to='catalog.Parameter', through='catalog.DatasetParameter'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='source',
            field=models.ForeignKey(blank=True, to='catalog.Source', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('platform', 'instrument')]),
        ),
    ]

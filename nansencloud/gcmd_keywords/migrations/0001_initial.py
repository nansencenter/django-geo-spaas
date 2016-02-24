# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from nansencloud.gcmd_keywords.models import Instrument
from nansencloud.gcmd_keywords.models import Platform
from nansencloud.gcmd_keywords.models import ScienceKeyword
from nansencloud.gcmd_keywords.models import DataCenter
from nansencloud.gcmd_keywords.models import HorizontalDataResolution
from nansencloud.gcmd_keywords.models import VerticalDataResolution
from nansencloud.gcmd_keywords.models import TemporalDataResolution
from nansencloud.gcmd_keywords.models import Project
from nansencloud.gcmd_keywords.models import ISOTopicCategory
from nansencloud.gcmd_keywords.models import Location

def add_gcmd_platforms(apps, schema_editor):
    Platform.objects.create_from_gcmd_keywords()

def add_gcmd_instruments(apps, schema_editor):
    Instrument.objects.create_from_gcmd_keywords()

def add_gcmd_science_keywords(apps, schema_editor):
    ScienceKeyword.objects.create_from_gcmd_keywords()

def add_data_centers(apps, schema_editor):
    DataCenter.objects.create_from_gcmd_keywords()

def add_horizontal_data_resolutions(app, schema_editor):
    HorizontalDataResolution.objects.create_from_gcmd_keywords()

def add_vertical_data_resolutions(app, schema_editor):
    VerticalDataResolution.objects.create_from_gcmd_keywords()

def add_temporal_data_resolutions(app, schema_editor):
    TemporalDataResolution.objects.create_from_gcmd_keywords()

def add_projects(app, schema_editor):
    Project.objects.create_from_gcmd_keywords()

def add_iso_topic_categories(app, schema_editor):
    ISOTopicCategory.objects.create_from_gcmd_keywords()

def add_locations(app, schema_editor):
    Location.objects.create_from_gcmd_keywords()

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataCenter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bucket_level0', models.CharField(max_length=200)),
                ('bucket_level1', models.CharField(max_length=200)),
                ('bucket_level2', models.CharField(max_length=200)),
                ('bucket_level3', models.CharField(max_length=200)),
                ('short_name', models.CharField(max_length=50)),
                ('long_name', models.CharField(max_length=200)),
                ('data_center_url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='HorizontalDataResolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('range', models.CharField(max_length=220)),
            ],
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=100)),
                ('instrument_class', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100)),
                ('subtype', models.CharField(max_length=100)),
                ('short_name', models.CharField(max_length=20)),
                ('long_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ISOTopicCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50)),
                ('subregion1', models.CharField(max_length=50)),
                ('subregion2', models.CharField(max_length=50)),
                ('subregion3', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=100)),
                ('series_entity', models.CharField(max_length=100)),
                ('short_name', models.CharField(max_length=50)),
                ('long_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bucket', models.CharField(max_length=6)),
                ('short_name', models.CharField(max_length=80)),
                ('long_name', models.CharField(max_length=220)),
            ],
        ),
        migrations.CreateModel(
            name='ScienceKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=30)),
                ('topic', models.CharField(max_length=30)),
                ('term', models.CharField(max_length=30)),
                ('variable_level_1', models.CharField(max_length=30)),
                ('variable_level_2', models.CharField(max_length=30)),
                ('variable_level_3', models.CharField(max_length=30)),
                ('detailed_variable', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='TemporalDataResolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('range', models.CharField(max_length=220)),
            ],
        ),
        migrations.CreateModel(
            name='VerticalDataResolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('range', models.CharField(max_length=220)),
            ],
        ),
        migrations.RunPython(add_gcmd_instruments),
        migrations.RunPython(add_gcmd_platforms),
        migrations.RunPython(add_gcmd_science_keywords),
        migrations.RunPython(add_data_centers),
        migrations.RunPython(add_horizontal_data_resolutions),
        migrations.RunPython(add_vertical_data_resolutions),
        migrations.RunPython(add_temporal_data_resolutions),
        migrations.RunPython(add_projects),
        migrations.RunPython(add_iso_topic_categories),
        migrations.RunPython(add_locations),
        # TODO: Add the other GCMD lists...
    ]

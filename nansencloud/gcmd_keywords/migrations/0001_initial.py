# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import os, json
from nerscmetadata import gcmd_keywords

json_fn = os.path.join(gcmd_keywords.json_path,
        gcmd_keywords.json_filename)
if not os.path.isfile(json_fn):
    gcmd_keywords.write_json()

def add_gcmd_platforms(apps, schema_editor):
    Platform = apps.get_model("gcmd_keywords", "Platform")
    platforms = json.load(open(json_fn))['Platforms']
    # 'Category', 'Series_Entity', 'Short_Name', 'Long_Name'
    for category in platforms.keys():
        if category=='Revision':
            continue
        for series_entity in platforms[category].keys():
            for short_and_long_names in platforms[category][series_entity]:
                pp = Platform(
                    category = category,
                    series_entity = series_entity,
                    short_name = short_and_long_names[0],
                    long_name = short_and_long_names[1]
                )
                pp.save()

def add_gcmd_instruments(apps, schema_editor):
    Instrument = apps.get_model("gcmd_keywords", "Instrument")
    instruments = json.load(open(json_fn))['Instruments']
    # 'Category', 'Class', 'Type', 'Subtype', 'Short_Name', 'Long_Name'
    for category in instruments.keys():
        if category=='Revision':
            continue
        for iclass in instruments[category].keys():
            for type in instruments[category][iclass].keys():
                for subtype in instruments[category][iclass][type].keys():
                    for short_and_long_names in instruments[category][iclass][type][subtype]:
                        ii = Instrument(
                            category = category,
                            instrument_class = iclass,
                            type = type,
                            subtype = subtype,
                            short_name = short_and_long_names[0],
                            long_name = short_and_long_names[1]
                        )
                        ii.save()

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
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
            name='Platform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=100)),
                ('series_entity', models.CharField(max_length=100)),
                ('short_name', models.CharField(max_length=50)),
                ('long_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.RunPython(add_gcmd_instruments),
        migrations.RunPython(add_gcmd_platforms),
    ]

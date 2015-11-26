# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import os, json
from nerscmetadata import gcmd_keywords

def add_gcmd_platforms(apps, schema_editor):
    Platform = apps.get_model('gcmd_keywords', 'Platform')
    for platform in gcmd_keywords.get_keywords('Platforms'):
        if platform.keys()[0]=='Revision':
            continue
        pp = Platform(
                category = platform['Category'],
                series_entity = platform['Series_Entity'],
                short_name = platform['Short_Name'],
                long_name = platform['Long_Name']
            )
        pp.save()

def add_gcmd_instruments(apps, schema_editor):
    Instrument = apps.get_model('gcmd_keywords', 'Instrument')
    for instrument in gcmd_keywords.get_keywords('Instruments'):
        if instrument.keys()[0]=='Revision':
            continue
        ii = Instrument(
                category = instrument['Category'],
                instrument_class = instrument['Class'],
                type = instrument['Type'],
                subtype = instrument['Subtype'],
                short_name = instrument['Short_Name'],
                long_name = instrument['Long_Name']
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

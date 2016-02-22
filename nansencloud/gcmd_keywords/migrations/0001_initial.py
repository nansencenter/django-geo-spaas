# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import os, json
from pythesint import gcmd_thesaurus

def add_gcmd_platforms(apps, schema_editor):
    Platform = apps.get_model('gcmd_keywords', 'Platform')
    for platform in gcmd_thesaurus.get_list('Platforms'):
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
    for instrument in gcmd_thesaurus.get_list('Instruments'):
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

def add_gcmd_science_keywords(apps, schema_editor):
    sciencekw = apps.get_model('gcmd_keywords', 'ScienceKeyword')
    for skw in gcmd_thesaurus.get_list('ScienceKeyword'):
        if instrument.keys()[0]=='Revision':
            continue
        ii = ScienceKeyword(
                category = skw['Category'],
                topic = skw['Topic'],
                term = skw['Term'],
                variable_level_1 = skw['Variable_Level_1'],
                variable_level_2 = skw['Variable_Level_2'],
                variable_level_3 = skw['Variable_Level_3'],
                detailed_variable = skw['Detailed_Variable'],
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
        migrations.RunPython(add_gcmd_science_keywords),
    ]

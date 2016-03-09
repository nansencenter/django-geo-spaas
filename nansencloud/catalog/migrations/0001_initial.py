# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vocabularies', '0001_initial'),
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
                ('ISO_topic_category', models.ForeignKey(to='vocabularies.ISOTopicCategory')),
                ('data_center', models.ForeignKey(to='vocabularies.DataCenter')),
                ('gcmd_location', models.ForeignKey(blank=True, to='vocabularies.Location', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DatasetParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset', models.ForeignKey(to='catalog.Dataset')),
                ('parameter', models.ForeignKey(to='vocabularies.Parameter')),
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
                ('uri', models.URLField(unique=True, validators=[django.core.validators.URLValidator(schemes=['http', 'https', 'ftp', 'ftps', b'file'])])),
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
                ('instrument', models.ForeignKey(to='vocabularies.Instrument')),
                ('platform', models.ForeignKey(to='vocabularies.Platform')),
            ],
        ),
        migrations.AddField(
            model_name='dataset',
            name='geographic_location',
            field=models.ForeignKey(blank=True, to='catalog.GeographicLocation', null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='parameters',
            field=models.ManyToManyField(to='vocabularies.Parameter', through='catalog.DatasetParameter'),
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

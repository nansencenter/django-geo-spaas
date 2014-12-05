# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Band',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sourceband', models.IntegerField()),
                ('name', models.CharField(max_length=100, blank=True)),
                ('standard_name', models.CharField(max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateTimeField(null=True, blank=True)),
                ('stop_date', models.DateTimeField(null=True, blank=True)),
                ('mapper', models.CharField(max_length=100, blank=True)),
                ('border', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('bands', models.ManyToManyField(to='cat.Band')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.IntegerField(default=0, choices=[(0, b'Filesystem'), (1, b'OpenDAP'), (2, b'FTP'), (3, b'HTTP'), (4, b'HTTPS')])),
                ('address', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Satellite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Search',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sdate', models.DateTimeField(null=True, blank=True)),
                ('date0', models.DateField()),
                ('date1', models.DateField()),
                ('polygon', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('satellite', models.ForeignKey(blank=True, to='cat.Satellite', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sensor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('location', models.ForeignKey(to='cat.Location')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=0, choices=[(0, b'Good'), (1, b'Bad')])),
                ('message', models.TextField(default=b'')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='sourcefile',
            unique_together=set([('name', 'location')]),
        ),
        migrations.AddField(
            model_name='search',
            name='sensor',
            field=models.ForeignKey(blank=True, to='cat.Sensor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='search',
            name='status',
            field=models.ForeignKey(blank=True, to='cat.Status', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='satellite',
            field=models.ForeignKey(blank=True, to='cat.Satellite', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='sensor',
            field=models.ForeignKey(blank=True, to='cat.Sensor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='sourcefile',
            field=models.ForeignKey(to='cat.SourceFile', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='status',
            field=models.ForeignKey(blank=True, to='cat.Status', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='band',
            name='sourcefile',
            field=models.ForeignKey(to='cat.SourceFile'),
            preserve_default=True,
        ),
    ]

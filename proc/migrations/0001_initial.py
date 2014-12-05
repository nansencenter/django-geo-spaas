# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def add_sar_polarizations(apps, schema_editor):
    Polarization = apps.get_model("proc", "Polarization")
    pols = ['HH', 'HV', 'VH', 'VV']
    ii=1
    for p in pols:
        pp = Polarization(pk=ii,pol=p)
        ii += 1
        pp.save()

class Migration(migrations.Migration):

    dependencies = [
        ('cat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('webname', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MerisWeb',
            fields=[
                ('image_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cat.Image')),
                ('resolution', models.CharField(max_length=2)),
                ('level', models.CharField(max_length=1)),
                ('daily', models.BooleanField(default=False)),
                ('chain', models.ForeignKey(related_name=b'merisweb_imgs', blank=True, to='proc.Chain', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cat.image',),
        ),
        migrations.CreateModel(
            name='Polarization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pol', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProcSearch',
            fields=[
                ('search_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cat.Search')),
                ('chain', models.ForeignKey(related_name=b'procsearches', blank=True, to='proc.Chain', null=True)),
            ],
            options={
            },
            bases=('cat.search',),
        ),
        migrations.CreateModel(
            name='SARWeb',
            fields=[
                ('image_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cat.Image')),
                ('chain', models.ForeignKey(related_name=b'sar_web', to='proc.Chain')),
                ('image', models.ForeignKey(parent_link=True, related_name=b'proc_sarweb_related', to='cat.Image')),
                ('polarizations', models.ManyToManyField(to='proc.Polarization', null=True, blank=True)),
                ('quicklooks', models.ManyToManyField(related_name=b'sar_web', null=True, to='cat.SourceFile', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cat.image',),
        ),
        migrations.AddField(
            model_name='merisweb',
            name='image',
            field=models.ForeignKey(parent_link=True, related_name=b'proc_merisweb_related', to='cat.Image'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='merisweb',
            name='quicklook',
            field=models.ForeignKey(related_name=b'merisweb_imgs', blank=True, to='cat.SourceFile', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(add_sar_polarizations),
    ]

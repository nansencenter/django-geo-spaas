''' Module containing methods to add content to the gcmd models

"import nansencloud.gcmd_keywords.add_lists" in 0001_initial.py and add content
after the last CreateModel command in the initial migration. E.g.,

migrations.RunPython(nansencloud.gcmd_keywords.add_lists.add_gcmd_instruments),
migrations.RunPython(nansencloud.gcmd_keywords.add_lists.add_gcmd_platforms),
migrations.RunPython(nansencloud.gcmd_keywords.add_lists.add_gcmd_science_keywords),
'''
import pythesint
from nansencloud.gcmd_keywords.models import Instrument
from nansencloud.gcmd_keywords.models import Platform
from nansencloud.gcmd_keywords.models import ScienceKeyword
from nansencloud.gcmd_keywords.models import DataCenter

def add_gcmd_platforms(apps, schema_editor):
    #Platform = apps.get_model('gcmd_keywords', 'Platform')
    Platform.objects.create_from_gcmd_keywords()

def add_gcmd_instruments(apps, schema_editor):
    #Instrument = apps.get_model('gcmd_keywords', 'Instrument')
    Instrument.objects.create_from_gcmd_keywords()

def add_gcmd_science_keywords(apps, schema_editor):
    #sciencekw = apps.get_model('gcmd_keywords', 'ScienceKeyword')
    ScienceKeyword.objects.create_from_gcmd_keywords()

def add_data_centers(apps, schema_editor):
    #dcs = apps.get_model('gcmd_keywords', 'DataCenter')
    DataCenter.objects.create_from_gcmd_keywords()

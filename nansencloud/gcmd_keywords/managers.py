#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:
#
# Created:
# Last modified:
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import os, json
from pythesint import gcmd_thesaurus

from django.db import models

class PlatformManager(models.Manager):

    def create_from_gcmd_keywords(self):
        # 'Category', 'Series_Entity', 'Short_Name', 'Long_Name'
        num = 0
        for platform in gcmd_thesaurus.get_list('Platforms', update=True):
            if platform.keys()[0]=='Revision':
                continue
            pp, created = self.get_or_create(
                category = platform['Category'],
                series_entity = platform['Series_Entity'],
                short_name = platform['Short_Name'],
                long_name = platform['Long_Name']
            )
            if created: num+=1
        print("Successfully added %d new platforms" %num)

class InstrumentManager(models.Manager):

    def create_from_gcmd_keywords(self):
        # 'Category', 'Class', 'Type', 'Subtype', 'Short_Name', 'Long_Name'
        num = 0
        for instrument in gcmd_thesaurus.get_list('Instruments', update=True):
            if instrument.keys()[0]=='Revision':
                continue
            ii, created = self.get_or_create(
                category = instrument['Category'],
                instrument_class = instrument['Class'],
                type = instrument['Type'],
                subtype = instrument['Subtype'],
                short_name = instrument['Short_Name'],
                long_name = instrument['Long_Name']
            )
            if created: num+=1
        print("Successfully added %d new instruments" %num)

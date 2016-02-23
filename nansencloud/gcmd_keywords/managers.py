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
import pythesint

from django.db import models

class PlatformManager(models.Manager):

    def create_from_gcmd_keywords(self):
        # 'Category', 'Series_Entity', 'Short_Name', 'Long_Name'
        num = 0
        pythesint.update_vocabulary(pythesint.GCMD_PLATFORMS)
        for platform in pythesint.get_list(pythesint.GCMD_PLATFORMS):
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
        num = 0
        pythesint.update_vocabulary(pythesint.GCMD_INSTRUMENTS)
        for instrument in pythesint.get_list(pythesint.GCMD_INSTRUMENTS):
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

class ScienceKeywordManager(models.Manager):

    def create_from_gcmd_keywords(self):
        num = 0
        pythesint.update_vocabulary(pythesint.GCMD_SCIENCE_KEYWORDS)
        for skw in pythesint.get_list(pythesint.GCMD_SCIENCE_KEYWORDS):
            if skw.keys()[0]=='Revision':
                continue
            ii, created = self.get_or_create(
                category = skw['Category'],
                topic = skw['Topic'],
                term = skw['Term'],
                variable_level_1 = skw['Variable_Level_1'],
                variable_level_2 = skw['Variable_Level_2'],
                variable_level_3 = skw['Variable_Level_3'],
                detailed_variable = skw['Detailed_Variable'],
            )
            if created: num+=1
        print("Successfully added %d new science keywords" %num)

class DataCenterManager(models.Manager):

    def create_from_gcmd_keywords(self):
        num = 0
        pythesint.update_vocabulary(pythesint.GCMD_DATA_CENTERS)
        for dc in pythesint.get_list(pythesint.GCMD_DATA_CENTERS):
            if dc.keys()[0]=='Revision':
                continue
            dd, created = self.get_or_create(
                bucket_level0 = dc['Bucket_Level0'],
                bucket_level1 = dc['Bucket_Level1'],
                bucket_level2 = dc['Bucket_Level2'],
                bucket_level3 = dc['Bucket_Level3'],
                short_name = dc['Short_Name'],
                long_name = dc['Long_Name'],
                data_center_url = dc['Data_Center_URL'],
            )
            if created: num+=1
        print("Successfully added %d new data centers" %num)

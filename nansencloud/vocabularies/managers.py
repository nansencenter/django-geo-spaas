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
import pythesint as pti

from django.db import models

class ParameterManager(models.Manager):

    ''' Fields:
    standard_name
    short_name
    units 
    gcmd_science_keyword 
    '''

    def get_by_natural_key(self, stdname):
        return self.get(standard_name=stdname)

    def create_from_vocabularies(self):
        ''' Create parameter instances from the nersc wkv list.
        '''
        warnings.warn('''
        Because we do not yet have the mapping between the different
        vocabularies, the GCMD science keywords are not linked to the catalog
        parameter table
        ''')
        num = 0
        pti.update_wkv_variable()
        for wkv in pti.get_wkv_variable_list():
            pp, created = self.get_or_create(
                standard_name = wkv['standard_name'],
                short_name = wkv['short_name'],
                units = wkv['units']
            )
            if created: num+=1
        print("Added %d new parameters" %num)

class PlatformManager(models.Manager):

    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)

    def create_from_vocabularies(self):
        # 'Category', 'Series_Entity', 'Short_Name', 'Long_Name'
        num = 0
        pti.update_gcmd_platform()
        for platform in pti.get_gcmd_platform_list():
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

    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_instrument()
        for instrument in pti.get_gcmd_instrument_list():
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

    def get_by_natural_key(self, category, topic, term, variable_level_1,
            variable_level_2, variable_level_3):
        return self.get(category=category, topic=topic, term=term,
                variable_level_1=variable_level_1,
                variable_level_2=variable_level_2,
                variable_level_3=variable_level_3)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_science_keyword()
        for skw in pti.get_gcmd_science_keyword_list():
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

    def get_by_natural_key(self, sname):
        return self.get(short_name=sname)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_provider()
        for dc in pti.get_gcmd_provider_list():
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

class HorizontalDataResolutionManager(models.Manager):

    def get_by_natural_key(self, hrr):
        return self.get(range=hrr)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_horizontalresolutionrange()
        for hdr in pti.get_gcmd_horizontalresolutionrange_list():
            if hdr.keys()[0]=='Revision':
                continue
            hh, created = self.get_or_create(
                    range=hdr['Horizontal_Resolution_Range']
                )
            if created: num+=1
        print('Successfully added %d new horizontal data resolution ranges'
                %num)

class VerticalDataResolutionManager(models.Manager):

    def get_by_natural_key(self, vrr):
        return self.get(range=vrr)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_verticalresolutionrange()
        for vdr in pti.get_gcmd_verticalresolutionrange_list():
            if vdr.keys()[0]=='Revision':
                continue
            vv, created = self.get_or_create(
                    range=vdr['Vertical_Resolution_Range']
                )
            if created: num+=1
        print('Successfully added %d new vertical data resolution ranges' %num)

class TemporalDataResolutionManager(models.Manager):

    def get_by_natural_key(self, trr):
        return self.get(range=trr)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_temporalresolutionrange()
        for tdr in pti.get_gcmd_temporalresolutionrange_list():
            if tdr.keys()[0]=='Revision':
                continue
            tt, created = self.get_or_create(
                    range=tdr['Temporal_Resolution_Range']
                )
            if created: num+=1
        print('Successfully added %d new temporal data resolution ranges' %num)

class ProjectManager(models.Manager):

    def get_by_natural_key(self, bucket, short_name):
        return self.get(bucket=bucket, short_name=short_name)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_project()
        for p in pti.get_gcmd_project_list():
            if p.keys()[0]=='Revision':
                continue
            pp, created = self.get_or_create(
                bucket = p['Bucket'],
                short_name = p['Short_Name'],
                long_name = p['Long_Name']
            )
            if created: num+=1
        print('Successfully added %d new projects' %num)

class ISOTopicCategoryManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)

    def create_from_vocabularies(self):
        num = 0
        pti.update_iso19115_topic_category()
        for iso in pti.get_iso19115_topic_category_list():
            ii, created = self.get_or_create(
                    name = iso['iso_topic_category']
                )
            if created: num+=1
        print('Successfully added %d new ISO 19115 topic categories' %num)

class LocationManager(models.Manager):

    def get_by_natural_key(self, category, type, subregion1, subregion2,
            subregion3):
        return self.get(category=category, type=type, subregion1=subregion1,
                subregion2=subregion2, subregion3=subregion3)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_location()
        for loc in pti.get_gcmd_location_list():
            if loc.keys()[0]=='Revision':
                continue
            ll, created = self.get_or_create(
                category = loc['Location_Category'],
                type = loc['Location_Type'],
                subregion1 = loc['Location_Subregion1'],
                subregion2 = loc['Location_Subregion2'],
                subregion3 = loc['Location_Subregion3']
            )
            if created: num+=1
        print('Successfully added %d new locations' %num)


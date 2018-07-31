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
from __future__ import print_function

import os, json, warnings
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
            pp, created = self.get_or_create(wkv)
            if created: num+=1
        print("Successfully added %d new parameters" %num)

    def get_or_create(self, wkv, *args, **kwargs):
        """ Get or create parameter instance from input pythesint entry """
        return super(ParameterManager, self).get_or_create(
                standard_name = wkv['standard_name'],
                short_name = wkv['short_name'],
                units = wkv['units'])


class PlatformManager(models.Manager):

    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)

    def create_from_vocabularies(self):
        # 'Category', 'Series_Entity', 'Short_Name', 'Long_Name'
        num = 0
        pti.update_gcmd_platform()
        for platform in pti.get_gcmd_platform_list():
            if 'Revision' in platform.keys():
                continue
            pp, created = self.get_or_create(platform)
            if created: num+=1
        print("Successfully added %d new platforms" %num)

    def get_or_create(self, platform, *args, **kwargs):
        """ Get or create platform instance from input pythesint entry """
        return super(PlatformManager, self).get_or_create(
                category = platform['Category'],
                series_entity = platform['Series_Entity'],
                short_name = platform['Short_Name'],
                long_name = platform['Long_Name'])


class InstrumentManager(models.Manager):

    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_instrument()
        for instrument in pti.get_gcmd_instrument_list():
            if 'Revision' in instrument.keys():
                continue
            ii, created = self.get_or_create(instrument)
            if created: num+=1
        print("Successfully added %d new instruments" %num)

    def get_or_create(self, instrument, *args, **kwargs):
        """ Get or create instrument instance from input pythesint entry """
        return super(InstrumentManager, self).get_or_create(
            category = instrument['Category'],
            instrument_class = instrument['Class'],
            type = instrument['Type'],
            subtype = instrument['Subtype'],
            short_name = instrument['Short_Name'],
            long_name = instrument['Long_Name'])


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
            if 'Revision' in skw.keys():
                continue
            ii, created = self.get_or_create(skw)
            if created: num+=1
        print("Successfully added %d new science keywords" %num)

    def get_or_create(self, skw, *args, **kwargs):
        """ Get or create ScienceKeyword instance from input pythesint entry """
        return super(ScienceKeywordManager, self).get_or_create(
                category = skw['Category'],
                topic = skw['Topic'],
                term = skw['Term'],
                variable_level_1 = skw['Variable_Level_1'],
                variable_level_2 = skw['Variable_Level_2'],
                variable_level_3 = skw['Variable_Level_3'],
                detailed_variable = skw['Detailed_Variable'])


class DataCenterManager(models.Manager):

    def get_by_natural_key(self, sname):
        return self.get(short_name=sname)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_provider()
        for dc in pti.get_gcmd_provider_list():
            if 'Revision' in dc.keys():
                continue
            dd, created = self.get_or_create(dc)
            if created: num+=1
        print("Successfully added %d new data centers" %num)

    def get_or_create(self, dc, *args, **kwargs):
        """ Get or create DataCenter instance from input pythesint entry """
        return super(DataCenterManager, self).get_or_create(
                bucket_level0 = dc['Bucket_Level0'],
                bucket_level1 = dc['Bucket_Level1'],
                bucket_level2 = dc['Bucket_Level2'],
                bucket_level3 = dc['Bucket_Level3'],
                short_name = dc['Short_Name'],
                long_name = dc['Long_Name'],
                data_center_url = dc['Data_Center_URL'])


class HorizontalDataResolutionManager(models.Manager):

    def get_by_natural_key(self, hrr):
        return self.get(range=hrr)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_horizontalresolutionrange()
        for hdr in pti.get_gcmd_horizontalresolutionrange_list():
            if 'Revision' in hdr.keys():
                continue
            hh, created = self.get_or_create(hdr)
            if created: num+=1
        print('Successfully added %d new horizontal data resolution ranges'
                %num)

    def get_or_create(self, hdr, *args, **kwargs):
        """ Get or create HorizontalDataResolution instance from input pythesint entry """
        return super(HorizontalDataResolutionManager, self).get_or_create(
                    range=hdr['Horizontal_Resolution_Range'])


class VerticalDataResolutionManager(models.Manager):

    def get_by_natural_key(self, vrr):
        return self.get(range=vrr)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_verticalresolutionrange()
        for vdr in pti.get_gcmd_verticalresolutionrange_list():
            if 'Revision' in vdr.keys():
                continue
            vv, created = self.get_or_create(vdr)
            if created: num+=1
        print('Successfully added %d new vertical data resolution ranges' %num)

    def get_or_create(self, vdr, *args, **kwargs):
        """ Get or create VerticalDataResolution instance from input pythesint entry """
        return super(VerticalDataResolutionManager, self).get_or_create(
                    range=vdr['Vertical_Resolution_Range'])


class TemporalDataResolutionManager(models.Manager):

    def get_by_natural_key(self, trr):
        return self.get(range=trr)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_temporalresolutionrange()
        for tdr in pti.get_gcmd_temporalresolutionrange_list():
            if 'Revision' in tdr.keys():
                continue
            tt, created = self.get_or_create(tdr)
            if created: num+=1
        print('Successfully added %d new temporal data resolution ranges' %num)

    def get_or_create(self, tdr, *args, **kwargs):
        """ Get or create TemporalDataResolution instance from input pythesint entry """
        return super(TemporalDataResolutionManager, self).get_or_create(
                    range=tdr['Temporal_Resolution_Range'])


class ProjectManager(models.Manager):

    def get_by_natural_key(self, bucket, short_name):
        return self.get(bucket=bucket, short_name=short_name)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_project()
        for p in pti.get_gcmd_project_list():
            if 'Revision' in p.keys():
                continue
            pp, created = self.get_or_create(p)
            if created: num+=1
        print('Successfully added %d new projects' %num)

    def get_or_create(self, p, *args, **kwargs):
        """ Get or create Project instance from input pythesint entry """
        return super(ProjectManager, self).get_or_create(
                bucket = p['Bucket'],
                short_name = p['Short_Name'],
                long_name = p['Long_Name'])


class ISOTopicCategoryManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)

    def create_from_vocabularies(self):
        num = 0
        pti.update_iso19115_topic_category()
        for iso in pti.get_iso19115_topic_category_list():
            ii, created = self.get_or_create(iso)
            if created: num+=1
        print('Successfully added %d new ISO 19115 topic categories' %num)

    def get_or_create(self, iso, *args, **kwargs):
        """ Get or create ISOTopicCategory instance from input pythesint entry """
        return super(ISOTopicCategoryManager, self).get_or_create(
                    name = iso['iso_topic_category'])


class LocationManager(models.Manager):

    def get_by_natural_key(self, category, type, subregion1, subregion2,
            subregion3):
        return self.get(category=category, type=type, subregion1=subregion1,
                subregion2=subregion2, subregion3=subregion3)

    def create_from_vocabularies(self):
        num = 0
        pti.update_gcmd_location()
        for loc in pti.get_gcmd_location_list():
            if 'Revision' in loc.keys():
                continue
            ll, created = self.get_or_create(loc)
            if created: num+=1
        print('Successfully added %d new locations' %num)

    def get_or_create(self, loc, *args, **kwargs):
        """ Get or create Location instance from input pythesint entry """
        return super(LocationManager, self).get_or_create(
                category = loc['Location_Category'],
                type = loc['Location_Type'],
                subregion1 = loc['Location_Subregion1'],
                subregion2 = loc['Location_Subregion2'],
                subregion3 = loc['Location_Subregion3'])



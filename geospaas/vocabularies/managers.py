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

class VocabularyManager(models.Manager):
    """ Base abstract class for all Managers here """

    def update_and_get_list(self, get_list, update, force):
        """ Get list of Pythesint entires after an update if needed

        Parameters
        ----------
        get_lilst : func
            function to get lilst of Pythesint entries
        update : func
            function to update Pythesint

        Returns
        -------
        pti_list : list
            lilst of Pythesin entries

        """
        pti_list = get_list()
        if force==True or len(pti_list)==0:
            update()
        pti_list = [e for e in get_list() if not 'Revision' in e.keys()]
        return pti_list

    def create_instances(self, pti_list):
        """ Create instances in database

        Parameters
        ----------
        pti_list : list with Pythesint entries

        """
        num = 0
        for entry in pti_list:
            pp, created = self.get_or_create(entry)
            if created: num+=1
        print("Successfully added %d new entries" % num)

    def get_or_create(self, entry, *args, **kwargs):
        """ Get or create database instance from input pythesint entry """

        params = {key : entry[self.mapping[key]] for key in self.mapping}
        return super(VocabularyManager, self).get_or_create(**params)

    def create_from_vocabularies(self, force=False, **kwargs):
        """ Get instances Pythesint and create instances in database.

        Parameters
        ----------
        force : bool
            Force update of Vocabulary from Internet ?

        """
        pti_list = self.update_and_get_list(self.get_list, self.update, force)
        self.create_instances(pti_list)

class ParameterManager(VocabularyManager):
    get_list = pti.get_wkv_variable_list
    get_list2 = pti.get_cf_standard_name_list
    update = pti.update_wkv_variable
    update2 = pti.update_cf_standard_name
    mapping = dict(standard_name='standard_name',
                   short_name='short_name',
                   units='units')

    def create_from_vocabularies(self, force=False, **kwargs):
        """ Create parameter instances from the NERSC WKV list and CF-standard names.

        Have to override VocabularyManager.create_from_vocabularies in order to allow
        merge of CF-variable names and WKVs.

        """
        warnings.warn(''' Since we do not yet have the mapping between the different
        vocabularies, the GCMD science keywords are not linked to the catalog
        parameter table ''')
        pti_list1 = self.update_and_get_list(self.get_list, self.update, force)
        pti_list2 = self.update_and_get_list(self.get_list2, self.update2, force)
        # merge two lists
        l1_std = [l['standard_name'] for l in pti_list1]
        for l in pti_list2:
            if 'standard_name' in l and l['standard_name'] not in pti_list1:
                pti_list1.append(
                    dict(
                        standard_name=l['standard_name'],
                        short_name='',
                        units=l['canonical_units']))

        self.create_instances(pti_list1)

    def get_by_natural_key(self, standard_name):
        return self.get(standard_name=standard_name)


class PlatformManager(VocabularyManager):
    get_list = pti.get_gcmd_platform_list
    update = pti.update_gcmd_platform
    mapping = dict(category='Category',
                    series_entity='Series_Entity',
                    short_name='Short_Name',
                    long_name='Long_Name')



class InstrumentManager(VocabularyManager):
    get_list = pti.get_gcmd_instrument_list
    update = pti.update_gcmd_instrument
    mapping = dict(category='Category',
                    instrument_class='Class',
                    type='Type',
                    subtype='Subtype',
                    short_name='Short_Name',
                    long_name='Long_Name')



class ScienceKeywordManager(VocabularyManager):
    get_list = pti.get_gcmd_science_keyword_list
    update = pti.update_gcmd_science_keyword
    mapping = dict(category='Category',
                topic='Topic',
                term='Term',
                variable_level_1='Variable_Level_1',
                variable_level_2='Variable_Level_2',
                variable_level_3='Variable_Level_3',
                detailed_variable='Detailed_Variable')

    def get_by_natural_key(self, category, topic, term, variable_level_1,
            variable_level_2, variable_level_3):
        return self.get(category=category, topic=topic, term=term,
                variable_level_1=variable_level_1,
                variable_level_2=variable_level_2,
                variable_level_3=variable_level_3)


class DataCenterManager(VocabularyManager):
    get_list = pti.get_gcmd_provider_list
    update = pti.update_gcmd_provider
    mapping = dict(bucket_level0='Bucket_Level0',
                bucket_level1='Bucket_Level1',
                bucket_level2='Bucket_Level2',
                bucket_level3='Bucket_Level3',
                short_name='Short_Name',
                long_name='Long_Name',
                data_center_url='Data_Center_URL')

    def get_by_natural_key(self, sname):
        return self.get(short_name=sname)


class HorizontalDataResolutionManager(VocabularyManager):
    get_list = pti.get_gcmd_horizontalresolutionrange_list
    update = pti.update_gcmd_horizontalresolutionrange
    mapping = dict(range='Horizontal_Resolution_Range')

    def get_by_natural_key(self, hrr):
        return self.get(range=hrr)


class VerticalDataResolutionManager(VocabularyManager):
    get_list = pti.get_gcmd_verticalresolutionrange_list
    update = pti.update_gcmd_verticalresolutionrange
    mapping = dict(range='Vertical_Resolution_Range')

    def get_by_natural_key(self, vrr):
        return self.get(range=vrr)


class TemporalDataResolutionManager(VocabularyManager):
    get_list = pti.get_gcmd_temporalresolutionrange_list
    update = pti.update_gcmd_temporalresolutionrange
    mapping = dict(range='Temporal_Resolution_Range')

    def get_by_natural_key(self, trr):
        return self.get(range=trr)


class ProjectManager(VocabularyManager):
    get_list = pti.get_gcmd_project_list
    update = pti.update_gcmd_project
    mapping = dict(bucket='Bucket',
                short_name='Short_Name',
                long_name='Long_Name')

    def get_by_natural_key(self, bucket, short_name):
        return self.get(bucket=bucket, short_name=short_name)


class ISOTopicCategoryManager(VocabularyManager):
    get_list = pti.get_iso19115_topic_category_list
    update = pti.update_iso19115_topic_category
    mapping = dict(name='iso_topic_category')

    def get_by_natural_key(self, name):
        return self.get(name=name)


class LocationManager(VocabularyManager):
    get_list = pti.get_gcmd_location_list
    update = pti.update_gcmd_location
    mapping = dict(category='Location_Category',
                type='Location_Type',
                subregion1='Location_Subregion1',
                subregion2='Location_Subregion2',
                subregion3='Location_Subregion3')

    def get_by_natural_key(self, category, type, subregion1, subregion2, subregion3):
        return self.get(category=category, type=type, subregion1=subregion1,
                subregion2=subregion2, subregion3=subregion3)

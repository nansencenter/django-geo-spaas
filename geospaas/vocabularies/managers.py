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


import pythesint as pti
from django.db import models


class VocabularyManager(models.Manager):
    """ Base abstract class for all Managers here """

    STANDARD_NAME = 'standard_name'

    def update_and_get_list(self, get_list, update, force, version=None):
        """ Get list of Pythesint entires after an update if needed

        Parameters
        ----------
        get_list : func
            function to get list of Pythesint entries
        update : func
            function to update Pythesint

        Returns
        -------
        pti_list : list
            list of Pythesint entries

        """
        pti_list = None

        if not force:
            pti_list = get_list()

        if force or not pti_list:
            update(version=version)
            pti_list = get_list()

        filtered_list = [e for e in pti_list if not 'Revision' in e.keys()]
        return filtered_list

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
        params = {key : entry.get(self.mapping[key], '') for key in self.mapping}
        return super(VocabularyManager, self).get_or_create(**params)

    def create_from_vocabularies(self, force=False, versions=None, **kwargs):
        """ Get instances Pythesint and create instances in database.

        Parameters
        ----------
        force : bool
            Force update of Vocabulary from Internet ?

        """
        versions = versions if versions else {}
        pti_lists = (
            self.update_and_get_list(v['get_list'], v['update'], force, version=versions.get(k))
            for k, v in self.vocabularies.items()
        )
        merged_list = next(pti_lists)  # pti_lists is a generator
        for list_to_merge in pti_lists:
            for new_keyword in list_to_merge:
                standard_name = new_keyword.get(self.STANDARD_NAME)
                if standard_name:
                    # check if a keyword with the same standard_name
                    # already exists in the merged list. If not, add it
                    add_new_keyword = True
                    for existing_keyword in merged_list:
                        if standard_name == existing_keyword[self.STANDARD_NAME]:
                            add_new_keyword = False
                            break
                    if add_new_keyword:
                        merged_list.append(new_keyword)

        self.create_instances(merged_list)


class ParameterManager(VocabularyManager):
    vocabularies = {
        'wkv_variable': {
            'get_list': pti.get_wkv_variable_list,
            'update': pti.update_wkv_variable
        },
        'cf_standard_name': {
            'get_list': pti.get_cf_standard_name_list,
            'update': pti.update_cf_standard_name
        }
    }
    mapping = dict(standard_name='standard_name',
                   short_name='short_name',
                   units='units')

    def get_by_natural_key(self, standard_name):
        return self.get(standard_name=standard_name)


class PlatformManager(VocabularyManager):
    vocabularies = {
        'gcmd_platform': {
            'get_list': pti.get_gcmd_platform_list,
            'update': pti.update_gcmd_platform
        }
    }
    mapping = dict(category='Category',
                    series_entity='Series_Entity',
                    short_name='Short_Name',
                    long_name='Long_Name')



class InstrumentManager(VocabularyManager):
    vocabularies = {
        'gcmd_instrument': {
            'get_list': pti.get_gcmd_instrument_list,
            'update': pti.update_gcmd_instrument
        }
    }
    mapping = dict(category='Category',
                    instrument_class='Class',
                    type='Type',
                    subtype='Subtype',
                    short_name='Short_Name',
                    long_name='Long_Name')



class ScienceKeywordManager(VocabularyManager):
    vocabularies = {
        'gcmd_science_keyword': {
            'get_list': pti.get_gcmd_science_keyword_list,
            'update': pti.update_gcmd_science_keyword
        }
    }
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
    vocabularies = {
        'gcmd_provider': {
            'get_list': pti.get_gcmd_provider_list,
            'update': pti.update_gcmd_provider
        }
    }
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
    vocabularies = {
        'gcmd_horizontalresolutionrange': {
            'get_list': pti.get_gcmd_horizontalresolutionrange_list,
            'update': pti.update_gcmd_horizontalresolutionrange
        }
    }
    mapping = dict(range='Horizontal_Resolution_Range')

    def get_by_natural_key(self, hrr):
        return self.get(range=hrr)


class VerticalDataResolutionManager(VocabularyManager):
    vocabularies = {
        'gcmd_verticalresolutionrange': {
            'get_list': pti.get_gcmd_verticalresolutionrange_list,
            'update': pti.update_gcmd_verticalresolutionrange
        }
    }
    mapping = dict(range='Vertical_Resolution_Range')

    def get_by_natural_key(self, vrr):
        return self.get(range=vrr)


class TemporalDataResolutionManager(VocabularyManager):
    vocabularies = {
        'gcmd_temporalresolutionrange': {
            'get_list': pti.get_gcmd_temporalresolutionrange_list,
            'update': pti.update_gcmd_temporalresolutionrange
        }
    }
    mapping = dict(range='Temporal_Resolution_Range')

    def get_by_natural_key(self, trr):
        return self.get(range=trr)


class ProjectManager(VocabularyManager):
    vocabularies = {
        'gcmd_project': {
            'get_list': pti.get_gcmd_project_list,
            'update': pti.update_gcmd_project
        }
    }
    mapping = dict(bucket='Bucket',
                short_name='Short_Name',
                long_name='Long_Name')

    def get_by_natural_key(self, bucket, short_name):
        return self.get(bucket=bucket, short_name=short_name)


class ISOTopicCategoryManager(VocabularyManager):
    vocabularies = {
        'iso19115_topic_category': {
            'get_list': pti.get_iso19115_topic_category_list,
            'update': pti.update_iso19115_topic_category
        }
    }
    mapping = dict(name='iso_topic_category')

    def get_by_natural_key(self, name):
        return self.get(name=name)


class LocationManager(VocabularyManager):
    vocabularies = {
        'gcmd_location': {
            'get_list': pti.get_gcmd_location_list,
            'update': pti.update_gcmd_location
        }
    }
    mapping = dict(category='Location_Category',
                type='Location_Type',
                subregion1='Location_Subregion1',
                subregion2='Location_Subregion2',
                subregion3='Location_Subregion3')

    def get_by_natural_key(self, category, type, subregion1, subregion2, subregion3):
        return self.get(category=category, type=type, subregion1=subregion1,
                subregion2=subregion2, subregion3=subregion3)

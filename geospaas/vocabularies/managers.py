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

    def create_instances(self, vocabulary_name, pti_list, version=None):
        """ Create instances in database

        Parameters
        ----------
        pti_list : list with Pythesint entries

        """
        num = 0
        for entry in pti_list:
            pp, created = self.get_or_create(
                version=version,
                kind=vocabulary_name,
                data=entry)
            if created: num+=1
        print("Successfully added %d new entries" % num)

    def create_from_vocabularies(self, force=False, versions=None, **kwargs):
        """ Get instances Pythesint and create instances in database.

        Parameters
        ----------
        force : bool
            Force update of Vocabulary from Internet ?

        """
        versions = versions if versions else {}
        for vocabulary_name, methods in self.vocabularies.items():
            pti_list = self.update_and_get_list(
                methods['get_list'],
                methods['update'],
                force, version=versions.get(vocabulary_name))

            # retrieve version from downloaded pythesint vocabulary
            get_version = methods.get('get_version')
            if get_version is not None:
                current_voc_version = get_version()
            else:
                current_voc_version = None
            self.create_instances(vocabulary_name, pti_list, current_voc_version)


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

    def get_by_natural_key(self, standard_name):
        return self.get(data__standard_name=standard_name)


class KeywordManager(VocabularyManager):
    vocabularies = {
        'gcmd_platform': {
            'get_list': pti.get_gcmd_platform_list,
            'get_version': pti.get_gcmd_platform_version,
            'update': pti.update_gcmd_platform,
        },
        'gcmd_instrument': {
            'get_list': pti.get_gcmd_instrument_list,
            'get_version': pti.get_gcmd_instrument_version,
            'update': pti.update_gcmd_instrument
        },
        'gcmd_science_keyword': {
            'get_list': pti.get_gcmd_science_keyword_list,
            'get_version': pti.get_gcmd_science_keyword_version,
            'update': pti.update_gcmd_science_keyword
        },
        'gcmd_provider': {
            'get_list': pti.get_gcmd_provider_list,
            'get_version': pti.get_gcmd_provider_version,
            'update': pti.update_gcmd_provider
        },
        'gcmd_horizontalresolutionrange': {
            'get_list': pti.get_gcmd_horizontalresolutionrange_list,
            'get_version': pti.get_gcmd_horizontalresolutionrange_version,
            'update': pti.update_gcmd_horizontalresolutionrange
        },
        'gcmd_verticalresolutionrange': {
            'get_list': pti.get_gcmd_verticalresolutionrange_list,
            'get_version': pti.get_gcmd_verticalresolutionrange_version,
            'update': pti.update_gcmd_verticalresolutionrange
        },
        'gcmd_temporalresolutionrange': {
            'get_list': pti.get_gcmd_temporalresolutionrange_list,
            'get_version': pti.get_gcmd_temporalresolutionrange_version,
            'update': pti.update_gcmd_temporalresolutionrange
        },
        'gcmd_project': {
            'get_list': pti.get_gcmd_project_list,
            'get_version': pti.get_gcmd_project_version,
            'update': pti.update_gcmd_project
        },
        'iso19115_topic_category': {
            'get_list': pti.get_iso19115_topic_category_list,
            'get_version': pti.get_iso19115_topic_category_version,
            'update': pti.update_iso19115_topic_category
        },
        'gcmd_location': {
            'get_list': pti.get_gcmd_location_list,
            'get_version': pti.get_gcmd_location_version,
            'update': pti.update_gcmd_location
        },
    }

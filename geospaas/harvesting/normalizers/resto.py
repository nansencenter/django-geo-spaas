"""Normalizer for the metadata used in a resto API
(https://github.com/jjrom/resto)
"""

import dateutil
import dateutil.parser
import re

import geospaas.harvesting.normalizers.utils as utils

from .base import MetadataNormalizer


class RestoAPIMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset using resto
    attributes
    """

    name = 'resto'

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return dataset_info.metadata['title']

    @utils.raises(KeyError)
    def get_entry_id(self, dataset_info):
        return dataset_info.metadata['title']

    @utils.raises(KeyError)
    def get_summary(self, dataset_info):
        description_attributes = ('sensorMode', 'platform', 'instrument', 'startDate')
        summary_fields = {}

        description = ', '.join([
            f"{attribute}={dataset_info.metadata[attribute]}"
            for attribute in description_attributes
        ])
        summary_fields[utils.SUMMARY_FIELDS['description']] = description

        try:
            processing_level = dataset_info.metadata.get('processingLevel').replace('LEVEL', '')
            summary_fields[utils.SUMMARY_FIELDS['processing_level']] = processing_level
        except AttributeError:
            pass

        return utils.dict_to_string(summary_fields)

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['startDate']).replace(microsecond=0)

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['completionDate']).replace(microsecond=0)

    def _get_platform_lookup(self, dataset_info):
        platform = dataset_info.metadata.get('platform')
        if platform:
            match = re.match('^S1([A-Z])$', platform)
            if match:
                platform = f'SENTINEL-1{match.group(1)}'
            return {'kind': 'gcmd_platform', 'data__icontains': platform}
        else:
            return None

    def _get_instrument_lookup(self, dataset_info):
        instrument = dataset_info.metadata.get('instrument')
        if instrument:
            if instrument == 'SAR':
                platform = dataset_info.metadata.get('platform')
                if re.match('^S1[A-Z]$', platform):
                    instrument = 'SENTINEL-1 C-SAR'
            return {'kind': 'gcmd_instrument', 'data__icontains': instrument}
        else:
            return None

    def _get_provider_lookup(self, dataset_info):
        provider = dataset_info.metadata.get('organisationName')
        if provider is None:
            provider = 'ESA/EO'
        return {
            'kind': 'gcmd_provider',
            'data__icontains': provider}

    def get_keywords(self, dataset_info):
        lookups_getters = (
            self._get_platform_lookup,
            self._get_instrument_lookup,
            self._get_provider_lookup,
        )
        lookups = []
        for get_lookup in lookups_getters:
            lookup = get_lookup(dataset_info)
            if lookup is not None:
                lookups.append(lookup)
        return utils.find_keywords(lookups)

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        return dataset_info.metadata['geometry']

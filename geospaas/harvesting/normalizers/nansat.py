"""Normalizer for datasets read with Nansat"""
from datetime import timezone

import dateutil.parser

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class NansatMetadataNormalizer(MetadataNormalizer):
    """Normalizer for Nansat"""

    name = 'nansat'

    def get_entry_id(self, dataset_info):
        entry_id = dataset_info.metadata.get('entry_id')
        filename_match = None
        if not entry_id:
            filename_match = utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url)
        if filename_match:
            entry_id = filename_match.group(1)
        return entry_id

    def get_entry_title(self, dataset_info):
        return dataset_info.metadata.get('entry_title')

    def get_summary(self, dataset_info):
        return dataset_info.metadata.get('summary')

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(
            dataset_info.metadata['time_coverage_start']).replace(tzinfo=timezone.utc)

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(
            dataset_info.metadata['time_coverage_end']).replace(tzinfo=timezone.utc)

    def get_keywords(self, dataset_info):
        lookups = []
        platform = dataset_info.metadata.get('platform')
        instrument = dataset_info.metadata.get('instrument')
        provider = dataset_info.metadata.get('provider')
        gcmd_location = dataset_info.metadata.get('gcmd_location')
        iso_topic_category = dataset_info.metadata.get('ISO_topic_category')
        if platform:
            lookups.append({'kind': 'gcmd_platform', 'data__icontains': platform})
        if instrument:
            lookups.append({'kind': 'gcmd_instrument', 'data__icontains': instrument})
        if provider:
            lookups.append({'kind': 'gcmd_provider', 'data__icontains': provider})
        if gcmd_location:
            lookups.append({'kind': 'gcmd_location', 'data__icontains': gcmd_location})
        if iso_topic_category:
            lookups.append({'kind': 'iso19115_topic_category',
                            'data__icontains': iso_topic_category})
        return utils.find_keywords(lookups)

    def get_location_geometry(self, dataset_info):
        try:
            return dataset_info.metadata.get('location_geometry').wkt
        except AttributeError:
            return ''

    def get_dataset_parameters(self, dataset_info):
        try:
            return utils.create_parameter_list(dataset_info.metadata['dataset_parameters'])
        except KeyError:
            return []

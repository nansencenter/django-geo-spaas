"""Normalizer for CPOM altimetry"""

from datetime import datetime, timezone

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class CPOMAltimetryMetadataNormalizer(MetadataNormalizer):
    """Normalizer for CPOM altimetry file. Everything is hard-coded
    because there is close to no metadata in the file
    """

    name = 'cpom'

    def get_entry_title(self, dataset_info):
        return 'CPOM SLA'

    def get_entry_id(self, dataset_info):
        return "CPOM_DOT"

    def get_time_coverage_start(self, dataset_info):
        return datetime(2003, 1, 1, tzinfo=timezone.utc)

    def get_time_coverage_end(self, dataset_info):
        return datetime(2015, 1, 1, tzinfo=timezone.utc)

    def get_keywords(self, dataset_info):
        return utils.find_keywords((
            {
                'kind': 'gcmd_platform',
                'data__Category': 'Earth Observation Satellites',
                'data__Short_Name': '',
                'data__Long_Name': '',
                'data__Sub_Category': ''
            },
            {
                'kind': 'gcmd_instrument',
                'data__Type': 'Altimeters',
                'data__Class': 'Active Remote Sensing',
                'data__Subtype': '',
                'data__Category': 'Earth Remote Sensing Instruments',
                'data__Long_Name': '',
                'data__Short_Name': ''
            },
            {'kind': 'gcmd_provider', 'data__icontains': 'UC-LONDON/CPOM'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        return dataset_info.metadata.get('geometry', '')

    def get_dataset_parameters(self, dataset_info):
        return utils.create_parameter_list(['sea_surface_height_above_sea_level'])

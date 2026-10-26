"""Normalize metadata from CSV file from Radarsat2 facility"""

from datetime import timedelta

import dateutil.parser

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class Radarsat2CSVMetadataNormalizer(MetadataNormalizer):
    """Normalizer for metadata from CSV from Radarsat-2 searching
    facility
    """

    name = 'radarsat2'

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        keys = ['Title', 'Polarization', 'Beam Mode']
        return ' '.join([dataset_info.metadata[key] for key in keys])

    @utils.raises(KeyError)
    def get_entry_id(self, dataset_info):
        return dataset_info.metadata['Order Key']

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['Date'])

    def get_time_coverage_end(self, dataset_info):
        return self.get_time_coverage_start(dataset_info) + timedelta(minutes=5)

    def get_keywords(self, dataset_info):
        return utils.find_keywords((
            {'kind': 'gcmd_platform', 'data__icontains': 'RADARSAT-2'},
            {'kind': 'gcmd_instrument', 'data__icontains': 'C-SAR'},
            {'kind': 'gcmd_provider', 'data__icontains': 'CA/CSA'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        """ return a WKT string corresponding to the location of the dataset"""
        footprint = dataset_info.metadata['Footprint'].strip().split(' ')
        return (f"POLYGON(({footprint[0]} {footprint[1]}, {footprint[2]} {footprint[3]}, "
                f"{footprint[4]} {footprint[5]}, {footprint[6]} {footprint[7]}, "
                f"{footprint[8]} {footprint[9]}))")

    def get_dataset_parameters(self, dataset_info):
        return utils.create_parameter_list('surface_backwards_scattering_coefficient_of_radar_wave')

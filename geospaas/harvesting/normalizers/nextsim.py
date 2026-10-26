"""Normalizer for NextSIM datasets"""

import re
from datetime import timedelta, timezone

import dateutil.parser

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class NextsimMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a NextSIM GeoSPaaS Dataset
    """

    name = 'nextsim'

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return dataset_info.metadata['title']

    @utils.raises((AttributeError, KeyError))
    def get_entry_id(self, dataset_info):
        return re.match(
            r'^.*/(\d{8}_hr-nersc-MODEL-nextsimf-ARC-b\d{8}-fv\d{2}.\d).nc$',
            dataset_info.url
        ).group(1)

    def get_summary(self, dataset_info):
        """Get the dataset's summary if it is available in the
        metadata, otherwise use a default
        """
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']: (
                'The Arctic Sea Ice Analysis and Forecast system uses the neXtSIM stand-alone sea '
                'ice model running the Brittle-Bingham-Maxwell sea ice rheology on an adaptive '
                'triangular mesh of 10 km average cell length.'),
            utils.SUMMARY_FIELDS['processing_level']: '4',
            utils.SUMMARY_FIELDS['product']: 'ARCTIC_ANALYSISFORECAST_PHY_ICE_002_011'
        })

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_start(self, dataset_info):
        date = dateutil.parser.parse(dataset_info.metadata['field_date'])
        if not date.tzinfo:
            date = date.replace(tzinfo=timezone.utc)
        return date

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_end(self, dataset_info):
        return self.get_time_coverage_start(dataset_info) + timedelta(days=1)

    def get_keywords(self, dataset_info):
        return utils.find_keywords((
            {
                'kind': 'gcmd_platform',
                'data__Category': 'Models',
                'data__Short_Name': 'OPERATIONAL MODELS',
            },
            {
                'kind': 'gcmd_instrument',
                'data__Long_Name': 'Computer',
                'data__Short_Name': 'Computer',
            },
            {'kind': 'gcmd_provider', 'data__Short_Name': 'NERSC'},
        ))

    def get_location_geometry(self, dataset_info):
        return utils.wkt_polygon_from_wgs84_limits('90', '62', '180', '-180')

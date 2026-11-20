"""Normalizer for the downscaled ECMWF seasonal forecasts"""

import re
from datetime import datetime, timezone

import dateutil.parser
from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils

from .base import MetadataNormalizer


class DownscaledECMWFMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset from a downscaled
    ECMWF seasonal forecast netcdf file
    """

    name = 'downscaled_ecmwf'

    def get_entry_title(self, dataset_info):
        return 'Downscaled ECMWF seasonal forecast'

    @utils.raises((AttributeError, KeyError))
    def get_entry_id(self, dataset_info):
        return re.match(
            r'^.*[/\\](Seasonal_[a-zA-Z]{3}[0-9]{2}_[a-zA-Z]+_n[0-9]+).nc$',
            dataset_info.url
        ).group(1)

    def get_summary(self, dataset_info):
        """Get the dataset's summary if it is available in the
        metadata, otherwise use a default
        """
        return "Downscaled version of ECMWF's seasonal forecasts"

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_start(self, dataset_info):
        creation_date = dateutil.parser.parse(dataset_info.metadata['date'])
        return datetime(creation_date.year, creation_date.month, 1,
                        tzinfo=creation_date.tzinfo or timezone.utc)

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_end(self, dataset_info):
        return self.get_time_coverage_start(dataset_info) + relativedelta(months=6)

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
        return ''

"""Normalizer for the metadata of ESA CCI datasets"""

import re

from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class MarineHeatWavesMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for a NOAA marine
    heatwaves dataset
    """

    name = 'noaa_marine_heatwaves'

    def get_entry_title(self, dataset_info):
        return 'NOAA marine heatwaves'

    @utils.raises(AttributeError)
    def get_entry_id(self, dataset_info):
        return utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        return ('Marine heatwaves product derived by applying the Marine Heatwave algorithm of '
                'Hobday et al. (2018)1 to the CRW daily global 5km CoralTemp satellite SST data '
                'product')

    time_patterns = (
        (
            re.compile(r'/noaa-crw_mhw.*' + utils.YEARMONTHDAY_REGEX + r'\.nc$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(days=1))
        ),
    )

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return utils.find_time_coverage(self.time_patterns, dataset_info.url)[0]

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return utils.find_time_coverage(self.time_patterns, dataset_info.url)[1]

    def get_keywords(self, dataset_info):
        return utils.find_keywords((
            {'kind': 'gcmd_platform', 'data__icontains': 'Earth Observation Satellites'},
            {'kind': 'gcmd_instrument', 'data__icontains': 'Imaging Spectrometers/Radiometers'},
            {'kind': 'gcmd_provider', 'data__icontains': 'DOC/NOAA'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    def get_location_geometry(self, dataset_info):
        return utils.WORLD_WIDE_COVERAGE_WKT

    def get_dataset_parameters(self, dataset_info):
        return []

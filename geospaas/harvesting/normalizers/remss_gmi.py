"""Normalizer for the metadata of REMSS GMI datasets"""

import re
from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class REMSSGMIMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for a REMSS GMI
    dataset
    """

    name = 'remss_gmi'

    def get_entry_title(self, dataset_info):
        return 'Atmosphere parameters from Global Precipitation Measurement Microwave Imager'

    @utils.raises((KeyError, AttributeError))
    def get_entry_id(self, dataset_info):
        return re.search(r'([^/]+)\.gz$', dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']:
            'GMI is a dual-polarization, multi-channel, conical-scanning, passive '
            'microwave radiometer with frequent revisit times.',
            utils.SUMMARY_FIELDS['processing_level']: '3'
        })

    time_patterns = (
        (
            re.compile(r'/y\d{4}/m\d{2}/f35_' + utils.YEARMONTHDAY_REGEX + r'v[\d.]+\.gz$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(days=1))
        ),
        (
            re.compile(r'/y\d{4}/m\d{2}/f35_' + utils.YEARMONTHDAY_REGEX + r'v[\d.]+_d3d\.gz$'),
            utils.create_datetime,
            lambda time: (time - relativedelta(days=2), time + relativedelta(days=1))
        ),
        (
            re.compile(r'/weeks/f35_' + utils.YEARMONTHDAY_REGEX + r'v[\d.]+\.gz$'),
            utils.create_datetime,
            lambda time: (time - relativedelta(days=6), time + relativedelta(days=1))
        ),
        (
            re.compile(r'/y\d{4}/m\d{2}/f35_' + utils.YEARMONTH_REGEX + r'v[\d.]+\.gz$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
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
            {'kind': 'gcmd_platform', 'data__Short_Name': 'GPM'},
            {'kind': 'gcmd_instrument', 'data__icontains': 'GMI'},
            {'kind': 'gcmd_provider', 'data__icontains': 'Remote Sensing Systems'},
        ))

    def get_location_geometry(self, dataset_info):
        return utils.WORLD_WIDE_COVERAGE_WKT

    def get_dataset_parameters(self, dataset_info):
        return utils.create_parameter_list((
            'wind_speed',
            'atmosphere_mass_content_of_water_vapor',
            'atmosphere_mass_content_of_cloud_liquid_water',
            'rainfall_rate'
        ))

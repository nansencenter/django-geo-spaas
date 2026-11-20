"""Normalizer for the metadata of GPortal GCOM-W datasets"""

import re
from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class GPortalGCOMWAMSR2MetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for a GCOM-W AMSR2
    dataset
    """

    name = 'gportal_gcom'

    def get_entry_title(self, dataset_info):
        return 'GCOM-W AMSR2'

    @utils.raises((AttributeError, KeyError))
    def get_entry_id(self, dataset_info):
        return utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        result = {utils.SUMMARY_FIELDS['description']: 'GCOM-W AMSR2 data'}
        processing_level_match = re.match(r'^.*/L([1-3][A-Z]?)(\.[^/]+)?/.*$', dataset_info.url)
        if processing_level_match:
            result[utils.SUMMARY_FIELDS['processing_level']] = processing_level_match.group(1)
        return utils.dict_to_string(result)

    time_patterns = (
        (
            re.compile(r'/[A-Z\d]+_' + utils.YEARMONTHDAY_REGEX + r'_\d{2}D.*\.h5$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(days=1))
        ),
        (
            re.compile(r'/[A-Z\d]+_' + utils.YEARMONTH_REGEX + r'00_\d{2}M.*\.h5$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        (
            re.compile(r'/[A-Z\d]+_' +
                       utils.YEARMONTHDAY_REGEX +
                       r'(?P<hour>\d{2})' +
                       r'(?P<minute>\d{2})' +
                       r'_.*\.h5$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(minutes=50))
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
            {'kind': 'gcmd_platform', 'data__icontains': 'GCOM-W1'},
            {'kind': 'gcmd_instrument', 'data__icontains': 'AMSR2'},
            {'kind': 'gcmd_provider', 'data__icontains': 'JP/JAXA/EOC'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    def get_location_geometry(self, dataset_info):
        return utils.WORLD_WIDE_COVERAGE_WKT

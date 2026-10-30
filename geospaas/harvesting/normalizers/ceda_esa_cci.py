"""Normalizer for the metadata of ESA CCI datasets"""

import re
from datetime import datetime
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class CEDAESACCIMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for an ESA CCI
    climatology dataset hosted by CEDA
    """

    name = 'ceda_esa_cci'

    def get_entry_title(self, dataset_info):
        return 'ESA SST CCI OSTIA L4 Climatology'

    @utils.raises((KeyError, AttributeError))
    def get_entry_id(self, dataset_info):
        return utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']: (
                'This v2.1 SST_cci Climatology Data Record (CDR) consists of Level 4 daily'
                ' climatology files gridded on a 0.05 degree grid.'
            ),
            utils.SUMMARY_FIELDS['processing_level']: '4',
            utils.SUMMARY_FIELDS['product']: 'ESA SST CCI Climatology'
        })

    time_patterns = (
        (   # model data over a year, based on observations from 1982 to 2010
            re.compile(r'/D(?P<d>\d{3})-.*\.nc$'),
            lambda d: utils.create_datetime(1982, day_of_year=d),
            lambda time: (time, datetime(2010, time.month, time.day).replace(tzinfo=tzutc()))
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
            {
                'kind': 'gcmd_platform',
                'data__Category': 'Earth Observation Satellites',
                'data__Short_Name': '',
                'data__Long_Name': '',
                'data__Sub_Category': ''
            },
            {
                'kind': 'gcmd_instrument',
                'data__Subtype': 'Imaging Spectrometers/Radiometers',
                'data__Long_Name': '',
                'data__Short_Name': ''
            },
            {'kind': 'gcmd_provider', 'data__icontains': 'ESA/CCI'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    def get_location_geometry(self, dataset_info):
        return utils.WORLD_WIDE_COVERAGE_WKT

    def get_dataset_parameters(self, dataset_info):
        return utils.create_parameter_list(('sea_surface_temperature',))

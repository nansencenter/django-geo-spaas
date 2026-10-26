"""Normalizer for the metadata of REMSS MW SST datasets"""

import re
from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class REMSSMWSSTMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for a REMSS
    passive mivrowaves SST dataset
    """

    name = 'remss_mw_sst'

    def get_entry_title(self, dataset_info):
        return 'Sea surface temperature from passive microwave sensors'

    @utils.raises((KeyError, AttributeError))
    def get_entry_id(self, dataset_info):
        return re.search(utils.NC_H5_FILENAME_MATCHER, dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']:
            'Sea surface temperature from TMI, AMSR-E, AMSR2, WindSat, GMI',
            utils.SUMMARY_FIELDS['processing_level']: '4'
        })

    time_patterns = (
        (
            re.compile(utils.YEARMONTHDAY_REGEX + r'[0-9]{6}-REMSS-L4_GHRSST-SSTfnd-MW_OI-GLOB-v[0-9.]+-fv[0-9.]+\.nc$'),
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
            {
                'kind': 'gcmd_platform',
                'data__Category': 'Earth Observation Satellites',
                'data__Short_Name': '',
                'data__Long_Name': '',
                'data__Sub_Category': ''
            },
            {
                'kind': 'gcmd_instrument',
                'data__Type': '',
                'data__Class': '',
                'data__Subtype': '',
                'data__Category': 'Earth Remote Sensing Instruments',
                'data__Long_Name': '',
                'data__Short_Name': ''
            },
            {'kind': 'gcmd_provider', 'data__icontains': 'Remote Sensing Systems'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    def get_location_geometry(self, dataset_info):
        return utils.WORLD_WIDE_COVERAGE_WKT

    def get_dataset_parameters(self, dataset_info):
        return utils.create_parameter_list((
            'sea_surface_temperature',
        ))

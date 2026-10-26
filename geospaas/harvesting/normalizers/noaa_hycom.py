"""Normalizer for the metadata of NOAA HYCOM datasets"""

import re
from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer
from .errors import MetadataNormalizationError


class NOAAHYCOMMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for a NOAA HYCOM
    dataset
    """

    name = 'noaa_hycom'

    def get_entry_title(self, dataset_info):
        return 'Global Hybrid Coordinate Ocean Model (HYCOM)'

    @utils.raises((KeyError, AttributeError))
    def get_entry_id(self, dataset_info):
        return utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']:
                'This system provides 4-day forecasts at 3-hour time steps, updated at 00Z '
                'daily. Navy Global HYCOM has a resolution of 1/12 degree in the horizontal '
                'and uses hybrid (isopycnal/sigma/z-level) coordinates in the vertical. The '
                'output is interpolated onto a regular 1/12-degree grid horizontally and '
                '40 standard depth levels.',
            utils.SUMMARY_FIELDS['processing_level']: '4',
            utils.SUMMARY_FIELDS['product']: 'HYCOM'
        })

    time_patterns = (
        (
            re.compile(
                r'/hycom_glb_\w+_' +
                utils.YEARMONTHDAY_REGEX +
                r'00_t(?P<hours>\d{3})\.nc\.gz'),
            lambda year, month, day, hours: (
                utils.create_datetime(year, month, day) + relativedelta(hours=int(hours))),
            lambda time: (time, time + relativedelta(hours=3))
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
                'data__Category': 'Models',
                'data__Short_Name': 'OPERATIONAL MODELS',
            },
            {
                'kind': 'gcmd_instrument',
                'data__Long_Name': 'Computer',
                'data__Short_Name': 'Computer',
            },
            {'kind': 'gcmd_provider', 'data__Short_Name': 'DOC/NOAA/NWS/NCEP'},
        ))

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        locations = {
            'hycom_glb_regp01': 'POLYGON((-100.04 70.04, -100.04 -0.04, -49.96 -0.04, '
                                '-49.96 70.04, -100.04 70.04))',
            'hycom_glb_regp06': 'POLYGON((149.96 70.04, 149.96 9.96, 210.04 9.96, 210.04 70.04, '
                                '149.96 70.04))',
            'hycom_glb_regp07': 'POLYGON((-150.04 60.04, -150.04 9.96, -99.96 9.96, -99.96 60.04, '
                                '-150.04 60.04))',
            'hycom_glb_regp17': 'POLYGON((-180.04 80.02,-180.04 59.98,-119.96 59.98,-119.96 80.02,'
                                '-180.04 80.02))',
            'hycom_glb_sfc_u': utils.WORLD_WIDE_COVERAGE_WKT,
        }
        for prefix, location in locations.items():
            if prefix in dataset_info.url:
                return location
        raise MetadataNormalizationError(f"Could not find a location gemetry for {dataset_info.metadata}")

    def get_dataset_parameters(self, dataset_info):
        return utils.create_parameter_list((
            'sea_water_salinity',
            'sea_water_temperature',
            'sea_water_salinity_at_bottom',
            'sea_water_temperature_at_bottom',
            'sea_surface_height_above_geoid',
            'eastward_sea_water_velocity',
            'northward_sea_water_velocity'
        ))

"""Normalizer for the metadata of NOAA RTOFS datasets"""

import re
from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class NOAARTOFSMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset for a NOAA RTOFS
    dataset
    """

    name = 'noaa_rtofs'

    def get_entry_title(self, dataset_info):
        return 'Global operational Real-Time Ocean Forecast System'

    @utils.raises((KeyError, AttributeError))
    def get_entry_id(self, dataset_info):
        return re.search(r'(\d{8}/[^/]+)\.(nc|h5)(\.gz)?$', dataset_info.url).group(1)

    def get_summary(self, dataset_info):
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']:
                "Real Time Ocean Forecast System (RTOFS) Global is a data-assimilating "
                "nowcast-forecast system operated by the National Weather Service's National "
                "Centers for Environmental Prediction (NCEP).",
            utils.SUMMARY_FIELDS['processing_level']: '4',
            utils.SUMMARY_FIELDS['product']: 'RTOFS'
        })

    time_patterns = (
        (
            re.compile(
                rf'/rtofs\.{utils.YEARMONTHDAY_REGEX}/' +
                r'rtofs_glo_3dz_[nf](?P<hours>\d{3})_.*\.nc'),
            lambda year, month, day, hours: (
                utils.create_datetime(year, month, day) + relativedelta(hours=int(hours))),
            lambda time: (time, time)
        ),
        (
            re.compile(
                rf'/rtofs\.{utils.YEARMONTHDAY_REGEX}/' +
                r'rtofs_glo_2ds_n(?P<hours>\d{3})_.*\.nc'),
            # the .../rtofs.20210519/rtofs_glo_2ds_n000_prog.nc
            # file has the date 2021-05-18 00:00:00
            lambda year, month, day, hours: (
                utils.create_datetime(year, month, day)
                - relativedelta(days=1)
                + relativedelta(hours=int(hours))),
            lambda time: (time, time)
        ),
        (
            re.compile(
                rf'/rtofs\.{utils.YEARMONTHDAY_REGEX}/' +
                r'rtofs_glo_2ds_f(?P<hours>\d{3})_.*\.nc'),
            lambda year, month, day, hours: (
                utils.create_datetime(year, month, day)
                + relativedelta(hours=int(hours))),
            lambda time: (time, time)
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
        url = dataset_info.url
        if 'US_east' in url:
            return ('POLYGON (('
                    '-105.193603515625 0, -40.719970703125 0,'
                    '-40.719970703125 79.74808502197266,'
                    '-105.193603515625 79.74808502197266,'
                    '-105.193603515625 0))')
        elif 'US_west' in url:
            return ('POLYGON (('
                    '-157.9200439453125 10.02840137481689,'
                    '-74.239990234375 10.02840137481689,'
                    '-74.239990234375 74.57466888427734,'
                    '-157.9200439453125 74.57466888427734,'
                    '-157.9200439453125 10.02840137481689))')
        elif 'alaska' in url:
            return ('POLYGON (('
                    '-179.1199951171875 45.77324676513672,'
                    '-112.6572265625 45.77324676513672,'
                    '-112.6572265625 78.41667938232422,'
                    '-179.1199951171875 78.41667938232422,'
                    '-179.1199951171875 45.77324676513672))')
        else:
            return utils.WORLD_WIDE_COVERAGE_WKT

    @utils.raises(KeyError)
    def get_dataset_parameters(self, dataset_info):
        url = dataset_info.url
        parameters = []
        if 'rtofs_glo_2ds_' in url:
            if 'diag' in url:
                parameters = [
                    'sea_surface_height_above_geoid',
                    'barotropic_eastward_sea_water_velocity',
                    'barotropic_northward_sea_water_velocity',
                    'surface_boundary_layer_thickness',
                    'ocean_mixed_layer_thickness'
                ]
            elif 'prog' in url:
                parameters = [
                    'eastward_sea_water_velocity',
                    'northward_sea_water_velocity',
                    'sea_surface_temperature',
                    'sea_surface_salinity',
                    'sea_water_potential_density'
                ]
            elif 'ice' in url:
                parameters = [
                    'ice_coverage',
                    'ice_temperature',
                    'ice_thickness',
                    'ice_uvelocity',
                    'icd_vvelocity',
                ]
        elif 'rtofs_glo_3dz_' in url:
            parameters = [
                'eastward_sea_water_velocity',
                'northward_sea_water_velocity',
                'sea_surface_temperature',
                'sea_surface_salinity',
            ]
        return utils.create_parameter_list(parameters)

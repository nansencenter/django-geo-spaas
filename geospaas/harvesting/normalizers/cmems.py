import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer
from geospaas.vocabularies.models import Keyword


class CMEMSMetadataNormalizer(MetadataNormalizer):
    """Normalizer for CMEMS datasets"""

    name = 'cmems'

    time_patterns = (
        # dataset-specific time coverage
        (
            re.compile(rf'nrt_global_allsat_phy_l4_{utils.YEARMONTHDAY_REGEX}_'),
            utils.create_datetime,
            lambda time: (time - relativedelta(hours=12), time + relativedelta(hours=12))
        ),
        (
            re.compile(rf'dataset-uv-nrt-monthly_{utils.YEARMONTH_REGEX}T'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        (
            re.compile(rf'mercatorpsy4v3r1_gl12_mean_{utils.YEARMONTH_REGEX}_'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        (
            re.compile(
                r'mercatorpsy4v3r1_gl12_(thetao|so|uovo)_' +
                utils.YEARMONTHDAY_REGEX +
                r'_(?P<hour>\d{2})h_R'),
            utils.create_datetime,
            lambda time: (time, time)
        ),
        (
            re.compile(rf'{utils.YEARMONTHDAY_REGEX}_m-CMCC-'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        (
            re.compile(
                rf'CMEMS_v5r1_IBI_PHY_NRT_PdE_01mav_{utils.YEARMONTHDAY_REGEX}_'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        (
            re.compile(rf"{utils.YEARMONTHDAY_REGEX}" +
                        r"_mm-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.*"),
            utils.create_datetime,
            lambda time: (
                datetime(time.year, time.month, 1, tzinfo=time.tzinfo),
                datetime(time.year, time.month, 1, tzinfo=time.tzinfo) + relativedelta(months=1)
            )
        ),
        (
            re.compile(rf"{utils.YEARMONTHDAY_REGEX}" +
                        r"_ym-12km-NERSC-MODEL-TOPAZ4B-ARC-RAN.*"),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(years=1))
        ),
        (
            re.compile(rf"{utils.YEARMONTH_REGEX}" +
                        r"_mm-metno-MODEL-topaz5_ecosmo-ARC-.*"),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        (
            re.compile(rf'mfwamglocep_{utils.YEARMONTHDAY_REGEX}' +
                        r'(?P<hour>(00|12))_R[0-9]{8}_(00|12)H'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(hours=12))
        ),
        (
            re.compile(rf'mercatorbiomer4v2r1_global_mean_{utils.YEARMONTH_REGEX}$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
        # generic 1 day coverage
        (
            re.compile(rf'(^|[-_.:/]){utils.YEARMONTHDAY_REGEX}(\d{{6}})?([-_.:T]|$)'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(days=1))
        ),
        # generic 1 month coverage
        (
            re.compile(rf'(^|[-_.:/]){utils.YEARMONTH_REGEX}([-_.:T]|$)'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(months=1))
        ),
    )

    @utils.raises((AttributeError, TypeError))
    def get_entry_id(self, dataset_info):
        """Extract entry_id from URL"""
        return utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url).group(1)

    @utils.raises((KeyError,))
    def get_summary(self, dataset_info):
        """Build a summary from metadata fields"""
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']: dataset_info.metadata['product_info'].description,
            utils.SUMMARY_FIELDS['processing_level']: (
                dataset_info.metadata['product_info'].processing_level),
            utils.SUMMARY_FIELDS['product']: dataset_info.metadata['product_info'].product_id,
            'Dataset ID': dataset_info.metadata['cmems_dataset_name'],
        })

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return utils.find_time_coverage(self.time_patterns, dataset_info.url)[0]

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return utils.find_time_coverage(self.time_patterns, dataset_info.url)[1]

    def get_keywords(self, dataset_info):
        results = []
        cmems_kws = utils.find_keywords([{'kind': 'gcmd_provider', 'data__Short_Name': 'CMEMS'}])
        if cmems_kws:
            results.append(cmems_kws[0])

        search_strings = (
            dataset_info.metadata['cmems_dataset_name'],
            *dataset_info.metadata['product_info'].sources,
        )
        platform = None
        platforms = utils.find_keywords([{'kind': 'gcmd_platform', 'data__icontains': s}
                                         for s in search_strings])
        if platforms:
            platform = platforms[0]
            results.append(platform)

        if platform:
            try:
                category = platform.data['Category']
            except KeyError:
                category = platform.data['category']

            if 'Models' in category:
                results.append(Keyword.objects.filter(kind='gcmd_instrument',
                                                      data__Long_Name='Computer',
                                                      data__Short_Name='Computer').first())
            else:
                instruments = utils.find_keywords([{'kind': 'gcmd_instrument', 'data__icontains': s}
                                                for s in search_strings])
                if instruments:
                    results.append(instruments[0])

        return results

    def get_location_geometry(self, dataset_info):
        """Get the spatial coverage of the dataset"""
        bbox = dataset_info.metadata['variables'][0].bbox
        return utils.wkt_polygon_from_wgs84_limits(bbox[3], bbox[1], bbox[2], bbox[0])

    def get_dataset_parameters(self, dataset_info):
        """Get a list of normalized dataset variables"""
        search_names = []
        for variable in dataset_info.metadata['variables']:
            standard_name = variable.standard_name
            short_name = variable.short_name
            if standard_name:
                search_names.append(standard_name)
            elif short_name:
                search_names.append(short_name)
            else:
                self.logger.warning('No available name for the following variable, skipping: %s',
                                    variable)
                continue

        return utils.create_parameter_list(search_names)

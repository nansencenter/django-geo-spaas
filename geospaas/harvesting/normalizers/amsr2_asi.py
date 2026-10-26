"""Normalizer for ASI-AMSR2 sea ice concentration datasets from Uni
Bremen
"""

import re

from dateutil.relativedelta import relativedelta

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class AMSR2ASIMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of an ASI-AMSR2 GeoSPaaS Dataset"""

    name = 'amsr2_asi'

    time_patterns = (
        (
            re.compile(r'/asi-AMSR2-n6250-' + utils.YEARMONTHDAY_REGEX + r'-.*\.nc$'),
            utils.create_datetime,
            lambda time: (time, time + relativedelta(days=1))
        ),
    )

    def get_entry_title(self, dataset_info):
        return 'ASI sea ice concentration from AMSR2'

    @utils.raises((AttributeError, KeyError))
    def get_entry_id(self, dataset_info):
        return re.match(
            r'^.*/(asi-AMSR2-[ns]6250-[0-9]{8}-v[0-9.]+)\.nc$',
            dataset_info.url
        ).group(1)

    def get_summary(self, dataset_info):
        """Get the dataset's summary if it is available in the
        metadata, otherwise use a default
        """
        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']: (
                'Sea ice concentration retrieved with the ARTIST Sea Ice (ASI) algorithm (Spreen et'
                ' al., 2008) which is applied to microwave radiometer data of the sensor AMSR2 '
                '(Advanced Microwave Scanning Radiometer 2) on the JAXA satellite GCOM-W1.'),
            utils.SUMMARY_FIELDS['processing_level']: '3',
        })

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
            {'kind': 'gcmd_provider', 'data__icontains': 'U-BREMEN/IUP'},
            {'kind': 'gcmd_location', 'data__icontains': 'SEA SURFACE'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    @utils.raises((AttributeError, KeyError))
    def get_location_geometry(self, dataset_info):
        hemisphere = re.match(
            r'^.*/asi-AMSR2-([ns])6250-[0-9]{8}-v[0-9.]+\.nc$',
            dataset_info.url
        ).group(1)
        if hemisphere == 'n':
            location = utils.wkt_polygon_from_wgs84_limits('90', '40', '180', '-180')
        elif hemisphere == 's':
            location = utils.wkt_polygon_from_wgs84_limits('-90', '-40', '180', '-180')
        return location

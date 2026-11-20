"""Normalizer for OSISAF metadata"""

import re

import dateutil.parser
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class OSISAFMetadataNormalizer(MetadataNormalizer):
    """ Normalizer for the attributes of datasets provided by OSISAF """

    name = 'osisaf'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filename_matcher = re.compile(r"([^/]+)\.nc(\.dods)?$")

    @staticmethod
    def try_keys(keys_to_try, dataset_info):
        """Returns the first value whose key is found in the metadata
        """
        result = None
        for key in keys_to_try:
            try:
                result = dataset_info.metadata[key]
                break
            except KeyError:
                pass
        if result is None:
            raise KeyError("Keys unavailable in metadata: %s", keys_to_try)
        return result

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return dataset_info.metadata['title']

    @utils.raises((AttributeError, KeyError))
    def get_entry_id(self, dataset_info):
        return self.filename_matcher.search(dataset_info.url).group(1)

    @utils.raises(KeyError)
    def get_summary(self, dataset_info):
        summary_fields = {}
        summary_fields[utils.SUMMARY_FIELDS['description']] = self.try_keys(
            ('abstract', 'summary'), dataset_info)
        return utils.dict_to_string(summary_fields)

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(
            self.try_keys(('start_date', 'time_coverage_start'), dataset_info)
        ).replace(tzinfo=tzutc())

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(
            self.try_keys(('stop_date', 'time_coverage_end'), dataset_info)
        ).replace(tzinfo=tzutc())

    def _get_platform_lookup(self, dataset_info):
        try:
            platform = self.try_keys(('platform_name', 'platform'), dataset_info)
        except KeyError:
            platform = None
        if platform:
            lookup = { 'data__icontains': platform}
        else:
            lookup = {
                'data__Category': 'Earth Observation Satellites',
                'data__Short_Name': '',
                'data__Long_Name': '',
                'data__Sub_Category': ''
            }
        return {
            'kind': 'gcmd_platform',
            **lookup
        }

    def _get_instrument_lookup(self, dataset_info):
        lookup = {
            'data__Type': '',
            'data__Class': '',
            'data__Subtype': '',
            'data__Category': 'Earth Remote Sensing Instruments',
            'data__Long_Name': '',
            'data__Short_Name': ''
        }

        try:
            instrument = self.try_keys(('instrument_type', 'instrument'), dataset_info)
        except KeyError:
            instrument = None

        if instrument:
            lookup = {'data__icontains': instrument}
        elif 'product_name' in dataset_info.metadata.keys():
            if ('_ice_conc' in dataset_info.metadata['product_name']
                    or '_ice_type' in dataset_info.metadata['product_name']
                    or '_ice_edge' in dataset_info.metadata['product_name']):
                return {
                    'data__Type': 'Spectrometers/Radiometers',
                    'data__Class': 'Passive Remote Sensing',
                    'data__Subtype': 'Imaging Spectrometers/Radiometers',
                    'data__Category': 'Earth Remote Sensing Instruments',
                    'data__Long_Name': '',
                    'data__Short_Name': ''
                }
            elif 'amsr2ice_conc' in dataset_info.metadata['product_name']:
                lookup = {'data__icontains': 'AMSR2'}
            elif '_mr_ice_drift' in dataset_info.metadata['product_name']:
                lookup = {'data__icontains': 'AVHRR'}
        return {'kind': 'gcmd_instrument', **lookup}

    def _get_provider_lookup(self, dataset_info):
        return {
            'kind': 'gcmd_provider',
            'data__icontains': dataset_info.metadata.get('institution', 'EUMETSAT/OSISAF')}

    def get_keywords(self, dataset_info):
        lookups_getters = (
            self._get_platform_lookup,
            self._get_instrument_lookup,
            self._get_provider_lookup,
        )
        lookups = [get_lookup(dataset_info) for get_lookup in lookups_getters]
        return utils.find_keywords(lookups)

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        return utils.wkt_polygon_from_wgs84_limits(
            self.try_keys(('northernmost_latitude', 'northernsmost_latitude', 'geospatial_lat_max'),
                          dataset_info),
            self.try_keys(('southernmost_latitude', 'geospatial_lat_min'), dataset_info),
            self.try_keys(('easternmost_longitude', 'geospatial_lon_max'), dataset_info),
            self.try_keys(('westernmost_longitude', 'geospatial_lon_min'), dataset_info))

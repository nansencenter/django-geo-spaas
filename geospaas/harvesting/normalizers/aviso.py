"""Normalizer for the metadata used in AVISO altimetry files"""

import dateutil.parser

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer
from .errors import MetadataNormalizationError


class AVISOAltimetryMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset using AVISO
    attributes
    """

    name = 'aviso'

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return dataset_info.metadata['title']

    @utils.raises((AttributeError, KeyError))
    def get_entry_id(self, dataset_info):
        return utils.NC_H5_FILENAME_MATCHER.search(dataset_info.url).group(1)

    @utils.raises(KeyError)
    def get_summary(self, dataset_info):
        summary_fields = {}

        summary_fields[utils.SUMMARY_FIELDS['description']] = dataset_info.metadata['comment']

        processing_level = dataset_info.metadata['processing_level'].lstrip('Ll')
        summary_fields[utils.SUMMARY_FIELDS['processing_level']] = processing_level

        return utils.dict_to_string(summary_fields)

    @utils.raises((dateutil.parser.ParserError,))
    def get_time_coverage_start(self, dataset_info):
        keys = ('time_coverage_start', 'time_coverage_begin')
        for key in keys:
            if key in dataset_info.metadata:
                return dateutil.parser.parse(dataset_info.metadata[key])
        raise MetadataNormalizationError(f"{keys} not found in raw metadata")

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['time_coverage_end'])

    def get_keywords(self, dataset_info):
        lookups = [{'kind': 'gcmd_provider', 'data__icontains': 'AVISO'}]
        platform = dataset_info.metadata.get('platform')
        if platform:
            lookups.append({
                'kind': 'gcmd_platform',
                'data__icontains': platform
            })
        instrument = dataset_info.metadata.get('instrument')
        if instrument:
            lookups.append({
                'kind': 'gcmd_instrument',
                'data__icontains': instrument
            })
        return utils.find_keywords(lookups)

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        if 'geometry' in dataset_info.metadata:
            return dataset_info.metadata['geometry']
        elif set(['geospatial_lat_max', 'geospatial_lat_min',
                  'geospatial_lon_max', 'geospatial_lon_min']).issubset(dataset_info.metadata.keys()):
            return utils.wkt_polygon_from_wgs84_limits(
                dataset_info.metadata['geospatial_lat_max'],
                dataset_info.metadata['geospatial_lat_min'],
                dataset_info.metadata['geospatial_lon_max'],
                dataset_info.metadata['geospatial_lon_min'])
        else:
            return ''

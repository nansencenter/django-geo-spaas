"""Normalizer for the metadata used in the Earthdata CMR search API"""

import re

import dateutil
import dateutil.parser
import shapely.geometry

import geospaas.harvesting.normalizers.utils as utils

from .base import MetadataNormalizer


class EarthdataCMRMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset using
    Earthdata CMR attributes
    """

    name = 'earthdata_cmr'

    def get_entry_title(self, dataset_info):
        return self.get_entry_id(dataset_info)

    @utils.raises((KeyError, IndexError))
    def get_entry_id(self, dataset_info):
        try:
            return dataset_info.metadata['umm']['DataGranule']['Identifiers'][0]['Identifier'].rstrip('.nc')
        except KeyError:
            return dataset_info.metadata['umm']['GranuleUR']

    @utils.raises((KeyError, IndexError))
    def get_summary(self, dataset_info):
        summary_fields = {}
        description = ''
        umm = dataset_info.metadata['umm']

        try:
            for platform in umm['Platforms']:
                description += (
                    f"Platform={platform['ShortName']}, " +
                    ', '.join(f"Instrument={i['ShortName']}" for i in platform['Instruments']) +
                    ', ')
        except KeyError:
            pass
        description += f"Start date={umm['TemporalExtent']['RangeDateTime']['BeginningDateTime']}"

        summary_fields[utils.SUMMARY_FIELDS['description']] = description

        processing_level_match = re.match(
            r'^.*_L(\d[^_]*)_.*$',
            umm['CollectionReference'].get('ShortName', ''))
        if processing_level_match:
            summary_fields[
                utils.SUMMARY_FIELDS['processing_level']] = processing_level_match.group(1)

        return utils.dict_to_string(summary_fields)

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(
            dataset_info.metadata['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime'])

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(
            dataset_info.metadata['umm']['TemporalExtent']['RangeDateTime']['EndingDateTime'])

    def _get_platform_string(self, dataset_info):
        return dataset_info.metadata['umm']['Platforms'][0]['ShortName']

    def _get_instrument_string(self, dataset_info):
        return dataset_info.metadata['umm']['Platforms'][0]['Instruments'][0]['ShortName']

    def _get_provider_string(self, dataset_info):
        return dataset_info.metadata['meta']['provider-id']

    def get_keywords(self, dataset_info):
        vocabularies = (
            ('gcmd_platform', self._get_platform_string),
            ('gcmd_instrument', self._get_instrument_string),
            ('gcmd_provider', self._get_provider_string),
        )
        lookups = []
        for voc, get_term in vocabularies:
            try:
                search_term = get_term(dataset_info)
            except (KeyError, IndexError):
                search_term = None
            if search_term:
                lookups.append({
                    'kind': voc,
                    'data__icontains': search_term
                })
        return utils.find_keywords(lookups)

    @utils.raises((KeyError, IndexError))
    def get_location_geometry(self, dataset_info):
        geometries = []
        raw_geometry = (dataset_info.metadata['umm']['SpatialExtent']
                                ['HorizontalSpatialDomain']
                                ['Geometry'])
        try:
            for bounds in raw_geometry['BoundingRectangles']:
                geometries.append(utils.wkt_polygon_from_wgs84_limits(
                    bounds['NorthBoundingCoordinate'],
                    bounds['SouthBoundingCoordinate'],
                    bounds['EastBoundingCoordinate'],
                    bounds['WestBoundingCoordinate']))
        except KeyError:
            for gpolygon in raw_geometry['GPolygons']:
                boundary = [(p['Longitude'], p['Latitude'])
                            for p in gpolygon['Boundary']['Points']]
                try:
                    holes = [
                        [
                            (p['Longitude'], p['Latitude'])
                            for p in hole['Points']
                        ]
                        for hole in gpolygon['ExclusiveZone']['Boundaries']
                    ]
                except KeyError:
                    holes = []
                geometries.append(shapely.geometry.Polygon(boundary, holes).wkt)
        return f"GEOMETRYCOLLECTION({','.join(geometries)})"

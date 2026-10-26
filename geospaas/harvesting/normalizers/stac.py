"""Normalizer for the metadata used in a STAC API
(https://stacspec.org/en/)
"""
import dateutil
import dateutil.parser
import json
import re

import shapely

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer


class STACMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset using STAC
    attributes
    """

    name = 'stac'

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return dataset_info.metadata['id']

    @utils.raises(KeyError)
    def get_entry_id(self, dataset_info):
        return dataset_info.metadata['id']

    @utils.raises(KeyError)
    def get_summary(self, dataset_info):
        description_attributes = ('platform', 'instruments')
        summary_fields = {}

        description = ', '.join([
            f"{attribute}={dataset_info.metadata['properties'][attribute]}"
            for attribute in description_attributes
        ])
        summary_fields[utils.SUMMARY_FIELDS['description']] = description

        try:
            processing_level = (dataset_info.metadata['properties']
                                                     ['processing:level']
                                                     .replace('L', ''))
            summary_fields[utils.SUMMARY_FIELDS['processing_level']] = processing_level
        except (AttributeError, KeyError):
            pass

        return utils.dict_to_string(summary_fields)

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['properties']['start_datetime']).replace(microsecond=0)

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['properties']['end_datetime']).replace(microsecond=0)

    def get_keywords(self, dataset_info):
        # TODO: refine
        lookups = []
        platform = dataset_info.metadata['properties'].get('platform')
        if platform:
            lookups.append({'kind': 'gcmd_platform', 'data__icontains': platform})
        instruments = dataset_info.metadata['properties'].get('instruments')
        if instruments:
            for instrument in instruments:
                lookups.append({'kind': 'gcmd_instrument', 'data__icontains': instrument})
        provider = dataset_info.metadata['properties'].get('processing:facility')
        if provider:
            lookups.append({'kind': 'gcmd_provider', 'data__icontains': provider})

        return utils.find_keywords(lookups)

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        return shapely.to_wkt(
            shapely.from_geojson(json.dumps(dataset_info.metadata['geometry'])))

    def get_extra_urls(self, dataset_info):
        extra_urls = []
        for link in dataset_info.metadata.get('links', []):
            if 's3' in link.get('auth:refs', []):
                extra_urls.append(link.get('href'))
        return extra_urls

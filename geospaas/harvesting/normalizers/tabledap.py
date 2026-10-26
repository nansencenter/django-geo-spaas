"""Normalizer for ERDDAP's tabledap data"""
import dateutil.parser

import geospaas.harvesting.normalizers.utils as utils
from .base import MetadataNormalizer
from .errors import MetadataNormalizationError


class TableDAPMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset using tabledap
    attributes
    """

    name = 'tabledap'

    @staticmethod
    def get_product_attribute(product_metadata, attribute):
        """Extract the value of an attribute from tabledap product
        metadata
        """
        for row in product_metadata['table']['rows']:
            if row[2] == attribute:
                return row[4]
        raise MetadataNormalizationError(f'Could not find product attribute {attribute}')

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return self.get_product_attribute(dataset_info.metadata['product_metadata'], 'title')

    @utils.raises(KeyError)
    def get_entry_id(self, dataset_info):
        return dataset_info.metadata['entry_id']

    @utils.raises(KeyError)
    def get_summary(self, dataset_info):
        return self.get_product_attribute(dataset_info.metadata['product_metadata'], 'summary')

    @utils.raises(KeyError)
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['temporal_coverage'][0])

    @utils.raises(KeyError)
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['temporal_coverage'][1])

    def get_keywords(self, dataset_info):
        lookups = []
        source = self.get_product_attribute(dataset_info.metadata['product_metadata'], 'source')
        if source == 'Argo float':
            source = 'Argo-float'
        lookups.append({'kind': 'gcmd_platform', 'data__icontains': source},)

        institution = self.get_product_attribute(
            dataset_info.metadata['product_metadata'], 'institution')
        if institution == 'Argo':
            lookups.append({'kind': 'gcmd_project', 'data__Short_Name': 'ARGO'})
        else:
            lookups.append({'kind': 'gcmd_provider', 'data__icontains': institution})

        return utils.find_keywords(lookups)

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        return dataset_info.metadata['trajectory']

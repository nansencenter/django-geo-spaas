"""Serializers for the base geospaas API"""
import geospaas.catalog.models
import geospaas.vocabularies.models

import rest_framework.serializers

class TagSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Tag objects"""

    class Meta:
        model = geospaas.catalog.models.Tag
        fields = ['id', 'url', 'name', 'value']
        extra_kwargs = {
            'url': {'view_name': 'base_viewer:catalog:api:tag-detail'}
        }


class KeywordSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Keyword objects"""

    class Meta:
        model = geospaas.vocabularies.models.Keyword
        fields = ['id', 'url', 'version', 'kind', 'data']
        extra_kwargs = {
            'url': {'view_name': 'base_viewer:vocabularies:api:keyword-detail'}
        }


class DatasetSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Dataset objects"""

    class Meta:
        model = geospaas.catalog.models.Dataset
        fields = [
            'id',
            'url',
            'entry_id',
            'entry_title',
            'time_coverage_start',
            'time_coverage_end',
            'location',
            'summary',
            'tags',
            'keywords',
        ]
        extra_kwargs = {
            'url': {'view_name': 'base_viewer:catalog:api:dataset-detail'},
            'tags': {
                'view_name': 'base_viewer:catalog:api:tag-detail',
                'read_only': True,
                'many': True
            },
            'keywords': {
                'view_name': 'base_viewer:vocabularies:api:keyword-detail',
                'read_only': True,
                'many': True
            },
        }


class DatasetURISerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for DatasetURI objects"""
    class Meta:
        model = geospaas.catalog.models.DatasetURI
        fields = ['id', 'url', 'uri']

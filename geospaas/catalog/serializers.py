"""Serializers for the base geospaas API"""
import geospaas.catalog.models

import rest_framework.serializers

class TagSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Tag objects"""

    class Meta:
        model = geospaas.catalog.models.Tag
        fields = ['url', 'name', 'value']
        extra_kwargs = {
            'url': {'view_name': 'base_viewer:catalog:api:tag-detail'}
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
        ]
        extra_kwargs = {
            'url': {'view_name': 'base_viewer:catalog:api:dataset-detail'},
            'tags': {
                'view_name': 'base_viewer:catalog:api:tag-detail',
                'read_only': True,
                'many': True
            },
        }


class DatasetURISerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for DatasetURI objects"""
    class Meta:
        model = geospaas.catalog.models.DatasetURI
        # fields = '__all__'
        fields = ['uri']

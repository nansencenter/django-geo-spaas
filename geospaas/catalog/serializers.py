"""Serializers for the base geospaas API"""
import geospaas.catalog.models

import rest_framework.serializers


class DatasetSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Dataset objects"""
    class Meta:
        model = geospaas.catalog.models.Dataset
        # fields = '__all__'
        fields = [
            'entry_id',
            'entry_title',
            'time_coverage_start',
            'time_coverage_end',
            'location',
            'summary',
            # 'tags',
        ]


class DatasetURISerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for DatasetURI objects"""
    class Meta:
        model = geospaas.catalog.models.DatasetURI
        # fields = '__all__'
        fields = ['uri']

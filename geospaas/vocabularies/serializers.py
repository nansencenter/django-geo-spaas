"""Serializers for the vocabularies API"""
import geospaas.vocabularies.models

import rest_framework.serializers


class KeywordSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Keyword objects"""
    class Meta:
        model = geospaas.vocabularies.models.Keyword
        fields = ['id', 'url', 'version', 'kind', 'data']
        extra_kwargs = {
            'url': {'view_name': 'geospaas:vocabularies:api:keyword-detail'}
        }


class ParameterSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Parameter objects"""
    class Meta:
        model = geospaas.vocabularies.models.Parameter
        fields = ['id', 'url', 'version', 'kind', 'data', 'gcmd_science_keyword']
        extra_kwargs = {
            'url': {'view_name': 'geospaas:vocabularies:api:parameter-detail'},
            'gcmd_science_keyword': {
                'view_name': 'geospaas:vocabularies:api:keyword-detail',
                'read_only': True,
            },
        }

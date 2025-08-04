"""Serializers for the vocabularies API"""
import geospaas.vocabularies.models

import rest_framework.serializers


class KeywordSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Keyword objects"""

    class Meta:
        model = geospaas.vocabularies.models.Keyword
        fields = ['id', 'url', 'version', 'kind', 'data']
        extra_kwargs = {
            'url': {'view_name': 'base_viewer:vocabularies:api:keyword-detail'}
        }

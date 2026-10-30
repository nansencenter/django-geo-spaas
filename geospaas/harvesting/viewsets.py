import rest_framework.serializers
import rest_framework_filters
from django_filters.rest_framework.filters import CharFilter
from django.db import models
from rest_framework import routers
from rest_framework.viewsets import ModelViewSet

import geospaas.harvesting.models
import geospaas.harvesting.utils as utils


class ProviderSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """Serializer for Provider objects"""
    class Meta:
        model = geospaas.harvesting.models.Provider
        fields = ['id', 'url', 'name', 'config']

        extra_kwargs = {
            'url': {'view_name': 'geospaas:harvesting:api:provider-detail'}
        }

    def to_representation(self, instance):
        """Mask passwords"""
        serialized = super().to_representation(instance)
        serialized['config']['crawler'] = utils.mask_secrets(serialized['config']['crawler'])
        return serialized

class ProviderFilter(rest_framework_filters.FilterSet):
    """Filterset for providers"""
    class Meta:
        model = geospaas.harvesting.models.Provider
        fields = {
            'name': '__all__',
            'config': '__all__',
        }
        filter_overrides = {
            models.JSONField: {
                'filter_class': CharFilter
            }
        }

class ProviderViewSet(ModelViewSet):
    """ViewSet for Providers"""
    queryset = geospaas.harvesting.models.Provider.objects.all()
    serializer_class = ProviderSerializer
    filter_class = ProviderFilter

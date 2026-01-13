from rest_framework.viewsets import ModelViewSet

import geospaas.vocabularies.models as models
import geospaas.vocabularies.serializers as serializers
import geospaas.vocabularies.filters as filters


class KeywordViewSet(ModelViewSet):
    """API endpoint to view Keywords"""
    queryset = models.Keyword.objects.all()
    serializer_class = serializers.KeywordSerializer
    filterset_class = filters.KeywordFilter


class ParameterViewSet(ModelViewSet):
    """API endpoint to view Parameters"""
    queryset = models.Parameter.objects.all()
    serializer_class = serializers.ParameterSerializer
    filterset_class = filters.ParameterFilter

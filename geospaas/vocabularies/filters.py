"""Custom filters for the vocabularies API"""
import rest_framework_filters
from django.db import models
from django_filters.rest_framework.filters import CharFilter

import geospaas.vocabularies.models


class KeywordFilter(rest_framework_filters.FilterSet):
    """Filterset for keywords"""
    class Meta:
        model = geospaas.vocabularies.models.Keyword
        fields = {
            'id': '__all__',
            'version': '__all__',
            'kind': '__all__',
            'data': '__all__',
        }
        filter_overrides = {
            models.JSONField: {
                'filter_class': CharFilter
            }
        }

class ParameterFilter(rest_framework_filters.FilterSet):
    """Filterset for parameters"""
    gcmd_science_keyword = rest_framework_filters.RelatedFilter(
        KeywordFilter,
        field_name='gcmd_science_keyword',
        queryset=geospaas.vocabularies.models.Keyword.objects.all(),
        distinct=True)
    class Meta:
        model = geospaas.vocabularies.models.Parameter
        fields = {
            'id': '__all__',
            'version': '__all__',
            'kind': '__all__',
            'data': '__all__',
            'gcmd_science_keyword': '__all__',
        }
        filter_overrides = {
            models.JSONField: {
                'filter_class': CharFilter
            }
        }

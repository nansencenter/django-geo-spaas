"""Custom filters for the base geospaas API"""
import rest_framework_filters
from django.db import models
from django.contrib.gis.db.models import GeometryField
from django_filters.rest_framework.filters import CharFilter

import geospaas.catalog.models
import geospaas.vocabularies.models


class TagFilter(rest_framework_filters.FilterSet):
    """Filterset for tags"""
    class Meta:
        model = geospaas.catalog.models.Tag
        fields = {
            'id': '__all__',
            'name': '__all__',
            'value': '__all__',
        }


class KeywordFilter(rest_framework_filters.FilterSet):
    """Filterset for keywords"""
    class Meta:
        model = geospaas.catalog.models.Keyword
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


class DatasetFilter(rest_framework_filters.FilterSet):
    """Filter for Datasets"""

    tags = rest_framework_filters.RelatedFilter(
        TagFilter,
        field_name='tags',
        queryset=geospaas.catalog.models.Tag.objects.all(),
        distinct=True)
    keywords = rest_framework_filters.RelatedFilter(
        KeywordFilter,
        field_name='keywords',
        queryset=geospaas.vocabularies.models.Keyword.objects.all(),
        distinct=True)

    class Meta:
        model = geospaas.catalog.models.Dataset
        filter_overrides = {
            GeometryField: {
                'filter_class': CharFilter
            }
        }
        fields = {
            'id': '__all__',
            'entry_id': '__all__',
            'summary': '__all__',
            'time_coverage_start': '__all__',
            'time_coverage_end': '__all__',
            'location': '__all__',
        }


class DatasetURIFilter(rest_framework_filters.FilterSet):
    """Filter for DatasetURIs"""
    dataset = rest_framework_filters.RelatedFilter(
        DatasetFilter,
        field_name='dataset',
        queryset=geospaas.catalog.models.Dataset.objects.all()
    )
    class Meta:
        model = geospaas.catalog.models.DatasetURI
        fields = {
            'uri': '__all__',
        }

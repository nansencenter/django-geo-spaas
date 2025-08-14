from django.urls import path, include
from rest_framework import routers
from rest_framework.viewsets import ModelViewSet

import geospaas.catalog.filters as filters
import geospaas.catalog.models as models
import geospaas.catalog.serializers as serializers


class DatasetViewSet(ModelViewSet):
    """API endpoint to view Datasets"""
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    filterset_class = filters.DatasetFilter


class DatasetURIViewSet(ModelViewSet):
    """API endpoint to view DatasetURIs"""
    queryset = models.DatasetURI.objects.all()
    serializer_class = serializers.DatasetURISerializer
    filterset_class = filters.DatasetURIFilter


class TagViewSet(ModelViewSet):
    """API endpoint to view Tags"""
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    filterset_class = filters.TagFilter


router = routers.DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'dataset_uris', DatasetURIViewSet)
router.register(r'datasets', DatasetViewSet)

urlpatterns = router.urls

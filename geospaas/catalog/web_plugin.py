from django.urls import include, path
from rest_framework import routers

import geospaas.catalog.viewsets as viewsets
from geospaas.catalog.views import CatalogView


router = routers.DefaultRouter()
router.register(r'tags', viewsets.TagViewSet)
router.register(r'dataset_uris', viewsets.DatasetURIViewSet)
router.register(r'datasets', viewsets.DatasetViewSet)


app_name = 'catalog'
urlpatterns = [
    path('', CatalogView.as_view(), name='geospaas_catalog'),
    path('api/', include((router.urls, 'api'))),
]
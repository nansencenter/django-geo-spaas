from django.urls import include, path
from rest_framework import routers

import geospaas.catalog.web_api as web_api
from geospaas.catalog.web_ui import CatalogView


router = routers.DefaultRouter()
router.register(r'tags', web_api.TagViewSet)
router.register(r'dataset_uris', web_api.DatasetURIViewSet)
router.register(r'datasets', web_api.DatasetViewSet)


app_name = 'catalog'
urlpatterns = [
    path('', CatalogView.as_view(), name='geospaas_catalog'),
    path('api/', include((router.urls, 'api'))),
]
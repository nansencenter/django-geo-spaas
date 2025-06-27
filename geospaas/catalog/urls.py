from django.urls import path, include
from django.urls import NoReverseMatch
from rest_framework import routers
from rest_framework.reverse import reverse
from rest_framework.response import Response

import geospaas.catalog.views as views

app_name = 'catalog'

router = routers.DefaultRouter()
router.register(r'dataset_uris', views.DatasetURIViewSet)
router.register(r'datasets', views.DatasetViewSet)

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('geometry/<int:pk>', views.get_geometry_geojson, name='geometry_geojson'),
    path('api/', include((router.urls, 'api'))),
]

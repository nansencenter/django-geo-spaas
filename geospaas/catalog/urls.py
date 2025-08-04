from django.urls import path, include
from rest_framework import routers

import geospaas.catalog.views as views


app_name = 'catalog'

router = routers.DefaultRouter()
router.register(r'tags', views.TagViewSet)
router.register(r'dataset_uris', views.DatasetURIViewSet)
router.register(r'datasets', views.DatasetViewSet)

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('api/', include((router.urls, 'api'))),
]

from django.urls import path, include
from rest_framework import routers

import geospaas.harvesting.viewsets as viewsets
from geospaas.harvesting.views import HarvestingView

router = routers.DefaultRouter()
router.register(r'providers', viewsets.ProviderViewSet)

app_name = 'harvesting'
urlpatterns = [
    path('', HarvestingView.as_view(), name='geospaas_harvesting'),
    path('api/', include((router.urls, 'api'))),
]

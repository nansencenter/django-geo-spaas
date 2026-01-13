from django.urls import path, include
from rest_framework import routers

import geospaas.vocabularies.viewsets as viewsets
from geospaas.vocabularies.views import VocabulariesView


router = routers.DefaultRouter()
router.register(r'keywords', viewsets.KeywordViewSet)
router.register(r'parameters', viewsets.ParameterViewSet)

app_name = 'vocabularies'
urlpatterns = [
    path('', VocabulariesView.as_view(), name='geospaas_vocabularies'),
    path('api/', include((router.urls, 'api'))),
]
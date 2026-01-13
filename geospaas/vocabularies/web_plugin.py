from django.urls import path, include
from rest_framework import routers

import geospaas.vocabularies.web_api as web_api
from geospaas.vocabularies.web_ui import VocabulariesView


router = routers.DefaultRouter()
router.register(r'keywords', web_api.KeywordViewSet)
router.register(r'parameters', web_api.ParameterViewSet)

app_name = 'vocabularies'
urlpatterns = [
    path('', VocabulariesView.as_view(), name='geospaas_vocabularies'),
    path('api/', include((router.urls, 'api'))),
]
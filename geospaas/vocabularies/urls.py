from django.urls import path, include
from rest_framework import routers


import geospaas.vocabularies.views as views

app_name = 'vocabularies'

router = routers.DefaultRouter()
router.register(r'keywords', views.KeywordViewSet)
router.register(r'parameters', views.ParameterViewSet)

urlpatterns = [
    path('api/', include((router.urls, 'api'))),
]

"""Views for vocabularies"""
from rest_framework.viewsets import ModelViewSet

import geospaas.vocabularies.models as models
import geospaas.vocabularies.serializers as serializers
import geospaas.vocabularies.filters as filters
from geospaas.base_viewer.views import GeoSPaaSView


class VocabulariesView(GeoSPaaSView):
    """"""
    template_name = 'vocabularies/vocabularies.html'
    tab_label = 'Vocabularies'

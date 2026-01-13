from django.urls import path

from geospaas.base_viewer.views import GeoSPaaSView


class VocabulariesView(GeoSPaaSView):
    """"""
    template_name = 'vocabularies/vocabularies.html'
    tab_label = 'Vocabularies'

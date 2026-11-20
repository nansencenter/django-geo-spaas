from django.urls import path

from geospaas.base_viewer.views import GeoSPaaSView


class HarvestingView(GeoSPaaSView):
    """"""
    template_name = 'geospaas_harvesting/harvesting.html'
    tab_label = 'Harvesting'

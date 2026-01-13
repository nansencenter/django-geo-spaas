import importlib

from django.views.generic import TemplateView
from django.urls import reverse

from geospaas.config import web_plugins


class GeoSPaaSView(TemplateView):
    """"""
    template_name = 'base_viewer/geospaas.html'
    tab_label = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geospaas_apps = []
        for module_name in web_plugins:
            module = importlib.import_module(module_name)
            self.geospaas_apps.append(module.app_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['geospaas_apps'] = self.geospaas_apps
        context['selected_tab'] = self.tab_label
        return context

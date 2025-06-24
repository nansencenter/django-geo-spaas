from django.views.generic import TemplateView
from django.urls import reverse


class GeoSPaaSView(TemplateView):
    """"""
    template_name = 'base_viewer/geospaas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['geospaas_apps'] = kwargs['geospaas_apps']
        context['selected_tab'] = kwargs['selected_tab']
        print('context', context)
        return context

    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)

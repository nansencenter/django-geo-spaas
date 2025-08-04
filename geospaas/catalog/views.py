from django.conf import settings
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

import geospaas.catalog.serializers as serializers
import geospaas.catalog.filters as filters
import geospaas.catalog.models as models
from geospaas.base_viewer.views import GeoSPaaSView
from .forms import BaseSearchForm



###### Website views ######
class IndexView(GeoSPaaSView):
    """ The class-based view for processing both GET and POST methods of basic version of viewer """
    form_class = BaseSearchForm
    main_template = 'catalog/ds_info.html'
    viewname = 'index'
    paginate_by = 20
    tab_label = 'Catalog'

    @classmethod
    def get_all_datasets(cls):
        """ Retrieve all dataset(s) from the database"""
        return models.Dataset.objects.order_by('time_coverage_start')

    @classmethod
    def get_filtered_datasets(cls, form):
        """ Retrieve filtered list of dataset(s) based on form inputs """
        ds = cls.get_all_datasets()
        return form.filter(ds)

    @classmethod
    def paginate(cls, ds, request):
        """ Paginate datasets and return paginator at current page"""
        paginator = Paginator(ds, cls.paginate_by)
        page_number = request.POST.get('page', 1)
        page_obj = paginator.get_page(page_number)
        return page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs['form']
        context['page_obj'] = kwargs['page_obj']
        context['show_local_address'] = getattr(settings, 'SHOW_LOCAL_ADDRESS', False)
        return context

    def get(self, request, *args, **kwargs):
        """ Render page if no data is given """
        form = self.form_class()
        form.is_valid()
        # ds = self.get_all_datasets()
        # page_obj = self.paginate(ds, request)
        page_obj = None
        context = self.get_context_data(form=form, page_obj=page_obj, **kwargs)
        return render(request, self.main_template, context)

    def post(self, request, *args, **kwargs):
        """ Render page when user submits search request """
        form = self.form_class(request.POST)
        form.is_valid()
        ds = self.get_filtered_datasets(form)
        page_obj = self.paginate(ds, request)
        context = self.set_context(form, page_obj)
        return render(request, self.main_template, context)


###### API views ######

class DatasetViewSet(ModelViewSet):
    """API endpoint to view Datasets"""
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    filterset_class = filters.DatasetFilter


class DatasetURIViewSet(ModelViewSet):
    """API endpoint to view DatasetURIs"""
    queryset = models.DatasetURI.objects.all()
    serializer_class = serializers.DatasetURISerializer
    filterset_class = filters.DatasetURIFilter


class TagViewSet(ModelViewSet):
    """API endpoint to view Tags"""
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    filterset_class = filters.TagFilter

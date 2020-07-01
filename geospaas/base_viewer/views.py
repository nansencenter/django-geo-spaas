from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View

from geospaas.base_viewer.forms import BaseSearchForm
from geospaas.catalog.models import Dataset, GeographicLocation


def get_geometry_geojson(request, pk, *args, **kwargs):
    """ Get GeographicLocation.Geometry as GeoJSON

    Parameters
    ----------
    pk : int
        primary key of GeographicLocation object

    Returns
    -------
    response : HttpResponse
        GeoJSON with geometry of GeographicLocation

    """
    gl = GeographicLocation.objects.filter(pk=pk)
    if gl.count() == 0:
        geojson = '{}'
    else:
        geojson = serialize('geojson', gl)
    return HttpResponse(geojson)


class IndexView(View):
    """ The class-based view for processing both GET and POST methods of basic version of viewer """
    form_class = BaseSearchForm
    main_template = 'base_viewer/elements.html'
    viewname = 'index'
    paginate_by = 2

    @classmethod
    def get_all_datasets(cls):
        """ Retrieve all dataset(s) from the database"""
        return Dataset.objects.all()

    @classmethod
    def get_filtered_datasets(cls, form):
        """ Retrieve filtered list of dataset(s) based on form inputs """
        ds = cls.get_all_datasets()
        return form.filter(ds)

    @classmethod
    def paginate(cls, ds, request):
        """ Paginate datasets and return paginator at current page"""
        paginator = Paginator(ds, cls.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        return page_obj

    @classmethod
    def set_context(cls, form, page_obj):
        """ Prepare all context for rendering """
        context = {}
        context['form'] = form
        context['page_obj'] = page_obj
        return context

    def get(self, request, *args, **kwargs):
        """ Render page if no data is given """
        form = self.form_class(request.session['post'])
        form.is_valid()
        ds = self.get_all_datasets()
        page_obj = self.paginate(ds, request)
        context = self.set_context(form, page_obj)

        context['session'] = request.session
        return render(request, self.main_template, context)

    def post(self, request, *args, **kwargs):
        """ Render page when user submits search request """
        form = self.form_class(request.POST)
        form.is_valid()
        ds = self.get_filtered_datasets(form)
        page_obj = self.paginate(ds, request)
        context = self.set_context(form, page_obj)
        request.session['post'] = request.POST
        context['session'] = request.session
        return render(request, self.main_template, context)

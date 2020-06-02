from django.shortcuts import render
from django.views.generic import View

from geospaas.base_viewer.forms import OverallForm
from geospaas.catalog.models import Dataset

# Create your views here.


class IndexView(View):

    form_class = OverallForm
    main_template = 'base_viewer/template_for_base.html'
    viewname = 'index'

    @classmethod
    def get_all_datasets(cls):
        return CatalogDataset.objects.all()

    @classmethod
    def get_filtered_datasets(cls, form):
        ds = cls.get_all_datasets()
        return form.filter(ds)

    @classmethod
    def set_context(cls, form, ds):
        context = {}
        context['form'] = form
        context['datasets'] = cls.set_dataset_context(ds)
        return context

    @classmethod
    def set_dataset_context(cls, ds):
        return ds  # excluded from other context for pagination development of django

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        form = self.form_class()
        form.is_valid()
        ds = self.get_all_datasets()
        context = self.set_context(form, ds)
        return render(request, self.main_template, context)

    def post(self, request, *args, **kwargs):
        ''' all sections needed for POST requests '''
        form = self.form_class(request.POST)
        form.is_valid()
        # modify ds based on the forms cleaned data
        ds = self.get_filtered_datasets(form)
        context = self.set_context(form, ds)
        return render(request, self.main_template, context)

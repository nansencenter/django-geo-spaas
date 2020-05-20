from django.shortcuts import render
from django.views.generic import View

from geospaas.base_viewer.forms import TimeAndSourceForm, SpatialSearchForm
from geospaas.catalog.models import Dataset as CatalogDataset

# Create your views here.


class IndexView(View):

    form_class = [TimeAndSourceForm, SpatialSearchForm,]
    main_template = 'base_viewer/template_for_base.html'
    viewname = 'index'
    #forms = list()

    @classmethod
    def create_forms(cls, *args):  # request_method='GET'
        ''' Set default values for the form by instantiating them '''
        return [i(*args) for i in cls.form_class]

    @classmethod
    def get_all_datasets(cls):
        return CatalogDataset.objects.all()

    @staticmethod
    def validate_forms(forms):
        for form in forms:  # for loop for making clean data by is_valid() method
            form.is_valid()
        return forms

    @classmethod
    def get_filtered_datasets(cls, forms):
        ds = cls.get_all_datasets()
        for form in forms:
            # using the filter function of each form sequentially
            ds = form.filter(ds)
        return ds

    @classmethod
    def set_context(cls, forms, ds):
        context = {}
        # setting the forms based on their class into the correct naming in the context
        for j in cls.form_class:
            for form in forms:
                if (isinstance(form.__class__(), j )):
                    context[j.__name__] = form

        context['datasets'] = cls.set_dataset_context(ds)
        return context

    @classmethod
    def set_dataset_context(cls, ds):
        return ds # excluded from other context for pagination development of django


    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        forms = self.create_forms()
        forms = self.validate_forms(forms)
        ds = self.get_all_datasets()
        context = self.set_context(forms, ds)
        return render(request, self.main_template, context)

    def post(self, request, *args, **kwargs):
        ''' all sections needed for POST requests'''

        forms = self.create_forms(request.POST)
        forms = self.validate_forms(forms)
        # modify ds based on the forms cleaned data
        ds = self.get_filtered_datasets(forms)
        context = self.set_context(forms, ds)
        return render(request, self.main_template, context)

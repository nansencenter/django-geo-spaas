from django.shortcuts import render
from django.views.generic import View

from geospaas.base_viewer.forms import BaseSearchForm
from geospaas.catalog.models import Dataset


class IndexView(View):
    """ The class-based view for processing both GET and POST methods of basic version of viewer """
    form_class = BaseSearchForm
    main_template = 'base_viewer/elements.html'
    viewname = 'index'

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
    def set_context(cls, form, ds):
        """ Prepare all context for rendering """
        context = {}
        context['form'] = form
        context['datasets'] = cls.set_dataset_context(ds)
        return context

    @classmethod
    def set_dataset_context(cls, ds):
        """ Prepare dataset context for rendering """
        return ds  # excluded from other context for pagination development of django

    def get(self, request, *args, **kwargs):
        """ Render page if no data is given """
        form = self.form_class()
        form.is_valid()
        ds = self.get_all_datasets()
        context = self.set_context(form, ds)
        return render(request, self.main_template, context)

    def post(self, request, *args, **kwargs):
        """ Render page when user submits search request """
        form = self.form_class(request.POST)
        form.is_valid()
        # modify ds based on the forms cleaned data
        ds = self.get_filtered_datasets(form)
        context = self.set_context(form, ds)
        return render(request, self.main_template, context)

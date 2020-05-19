from django.shortcuts import render
from django.views.generic import View

from geospaas.base_viewer.forms import TimeAndSourceForm, SpatialSearchForm
from geospaas.catalog.models import Dataset as CatalogDataset

#from geospaas.base_viewer.forms import Search_with_para_Form
# Create your views here.


class IndexView(View):

    form_class = [ TimeAndSourceForm, SpatialSearchForm,]
    main_template = 'base_viewer/template_for_base.html'
    viewname = 'index'
    forms = list()

    @classmethod
    def create_forms(cls, *args):#request_method='GET'
        ''' Set default values for the form by instantiating them '''
        return [i(*args) for i in cls.form_class]

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        forms = self.create_forms()
        self.validate_forms()
        #self.filtering_the_datasets(request)
        self.ds = self.get_all_datasets()
        self.set_context()
        return render(request, self.main_template, self.context)

    def post(self, request, *args, **kwargs):
        ''' all sections needed for POST requests'''

        #### instantiating with data of POST request
        ###self.forms = [i(request.POST) for i in self.form_class]
        self.create_forms(request.POST)

        self.validate_forms()

        # modify attributes based on the forms cleaned data
        self.ds = self.get_filtered_datasets()
        # return self.final_rendering(request)
        self.set_context()
        return render(request, self.main_template, self.context)

    def get_all_datasets(self):
        return CatalogDataset.objects.all()


    def validate_forms(self):
        for element_forms in self.forms:  # for loop for making clean data by is_valid() method
            element_forms.is_valid()
            for errorField in element_forms.errors:  # temporary error message
                print(f"errorField")

    def get_filtered_datasets(self):
        ds = self.get_all_datasets()
        for form in self.form_class:
            # using the filter function of each form sequentially
            ds = form.filter(ds)
        return ds

    def set_context(self):
        self.context = {}
        # initializing the list of the forms that passed into context
        # passing the form_list into context
        self.context['form_list'] = self.forms
        self.set_dataset_context()

    # excluded from other context for pagination development of django
    def set_dataset_context(self):
        self.context['datasets'] = self.ds

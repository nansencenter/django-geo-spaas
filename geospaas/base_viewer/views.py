from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from geospaas.base_viewer.forms import SearchFormBelow, SearchFormAbove
from geospaas.catalog.models import Dataset as CatalogDataset
#from geospaas.base_viewer.forms import Search_with_para_Form
# Create your views here.


class IndexView(View):

    # order of this list matters for showing propery in the templates with correct order
    form_class = [SearchFormAbove, SearchFormBelow, ]

    main_template = 'base_viewer/template_for_base.html'
    viewname = 'index'
    forms = list()
    context = {}

    def instantiation_and_set_form_defaults(self):
        ''' Set default values for the form by instantiating them '''
        # initialize the form list for setting default values
        self.forms = [None] * len(self.form_class)
        # loop for instantiating with defaults
        for counter, element_form_class in enumerate(self.form_class):
            self.forms[counter] = element_form_class({})  # instantiation
            self.forms[counter].set_defaults()  # setting the defaults

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        self.instantiation_and_set_form_defaults()
        self.validation_and_error_check()
        self.filtering_func(request)
        return self.final_rendering(request)

    def post(self, request, *args, **kwargs):
        ''' all sections needed for POST requests'''
        # initialize the form list for setting default values
        self.forms = [None] * len(self.form_class)

        # loop for instantiating with data of POST request
        for counter, element_form_class in enumerate(self.form_class):
            self.forms[counter] = element_form_class(request.POST)

        self.validation_and_error_check()

        # modify attributes based on the forms cleaned data
        self.filtering_func(request)
        return self.final_rendering(request)

    def validation_and_error_check(self):
        for element_forms in self.forms:  # for loop for making clean data by is_valid() method
            element_forms.is_valid()
            for errorField in element_forms.errors:  # temporary error message
                print(f"errorField")

    def filtering_func(self, request):
        ds = CatalogDataset.objects.all()
        if (request.method == 'POST'):
            for counter in range(len(self.form_class)):
                # using the filter function of each form sequentially
                ds = self.forms[counter].filter(ds)
            self.ds = ds
        elif (request.method == 'GET'):
            self.ds = ds

    def final_rendering(self, request):
        ''' Render page based on several forms of data as well as some other context '''
        self.context = {}
        self.set_context()
        return render(request, self.main_template, self.context)

    def set_context(self):
        # initializing the list of the forms that passed into context
        form_list = [None] * len(self.forms)
        for counter, value in enumerate(self.forms):
            # make the form_list elements one by one (form by form)
            form_list[counter] = value
        # passing the form_list into context
        self.context['form_list'] = form_list
        self.set_dataset_context()

    def set_dataset_context(self): # excluded from other context for pagination development of django
        self.context['datasets'] = self.ds

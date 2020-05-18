from django.shortcuts import render
from django.views.generic import View

from geospaas.base_viewer.forms import TimeAndSourceForm, SpatialSearchForm
from geospaas.catalog.models import Dataset as CatalogDataset

#from geospaas.base_viewer.forms import Search_with_para_Form
# Create your views here.


class IndexView(View):

    form_class = [SpatialSearchForm, TimeAndSourceForm, ]
    main_template = 'base_viewer/template_for_base.html'
    viewname = 'index'
    forms = list()

    def create_forms(self, *args):#request_method='GET'
        ''' Set default values for the form by instantiating them '''
        self.forms = [i(*args) for i in self.form_class]
        #if request_post is 'GET':
        #    request_post = dict()
        #if len(args)==0:
        #     # GET method
        #else:
        #    self.forms = [i(args[0]) for i in self.form_class] # POST method
        #return self.forms

        #### initialize the form list for setting default values
        #### loop for instantiating with defaults
        ###self.forms = [i({}) for i in self.form_class]
        ###for counter, element_form_class in enumerate(self.form_class):
        ###    self.forms[counter].set_defaults()  # setting the defaults

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        self.create_forms()
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
        self.ds = self.get_filtered_datasets(request)
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

    def get_filtered_datasets(self, request):
        ds = self.get_all_datasets()
        for counter in range(len(self.form_class)):
            # using the filter function of each form sequentially
            ds = self.forms[counter].filter(ds)
        return ds

    def set_context(self):
        self.context = {}
        # initializing the list of the forms that passed into context
        form_list = [i for i in self.forms]
        # passing the form_list into context
        self.context['form_list'] = form_list
        self.set_dataset_context()

    # excluded from other context for pagination development of django
    def set_dataset_context(self):
        self.context['datasets'] = self.ds

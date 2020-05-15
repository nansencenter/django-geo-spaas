from django.shortcuts import render
from django.utils import timezone
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

    def create_forms(self):
        ''' Set default values for the form by instantiating them '''
        # initialize the form list for setting default values
        # loop for instantiating with defaults
        self.forms = [i({}) for i in self.form_class]
        for counter, element_form_class in enumerate(self.form_class):
            self.forms[counter].set_defaults()  # setting the defaults

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        self.create_forms()
        self.validate_forms()
        self.filtering_the_datasets(request)
        self.set_context()
        return render(request, self.main_template, self.context)

    def post(self, request, *args, **kwargs):
        ''' all sections needed for POST requests'''

        # instantiating with data of POST request
        self.forms = [i(request.POST) for i in self.form_class]

        self.validate_forms()

        # modify attributes based on the forms cleaned data
        self.filtering_the_datasets(request)
        #return self.final_rendering(request)
        self.set_context()
        return render(request, self.main_template, self.context)

    def validate_forms(self):
        for element_forms in self.forms:  # for loop for making clean data by is_valid() method
            element_forms.is_valid()
            for errorField in element_forms.errors:  # temporary error message
                print(f"errorField")

    def filtering_the_datasets(self, request):
        ds = CatalogDataset.objects.all()
        if (request.method == 'POST'):
            for counter in range(len(self.form_class)):
                # using the filter function of each form sequentially
                ds = self.forms[counter].filter(ds)
            self.ds = ds
        elif (request.method == 'GET'):
            self.ds = ds

    def set_context(self):
        self.context = {}
        # initializing the list of the forms that passed into context
        form_list = [i for i in self.forms]
        ## passing the form_list into context
        self.context['form_list'] = form_list
        self.set_dataset_context()

    def set_dataset_context(self): # excluded from other context for pagination development of django
        self.context['datasets'] = self.ds

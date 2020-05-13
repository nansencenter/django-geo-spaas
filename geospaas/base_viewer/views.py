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

    def instantiation_and_set_form_defaults(self):
        ''' Set default values for the form by instantiating them '''
        # initialize the form list for setting default values
        self.forms = [None] * len(self.form_class)
        # loop for instantiating with defaults
        for counter, element_form_class in enumerate(self.form_class):
            # similar default values can be set via *elif* at the bottom of this statement
            if 'time_coverage_start' in element_form_class.Meta.fields:
                self.forms[counter] = element_form_class(
                    {'time_coverage_start':
                     timezone.datetime(2000, 1, 1, tzinfo=timezone.utc).date(),
                     'time_coverage_end': timezone.now().date(),
                     })
            # elif: ######## code here for other default values
                    ######## code here for other default values
            else:  # instantiating without default values
                self.forms[counter] = element_form_class({})


    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        # set default values of form
        self.instantiation_and_set_form_defaults()
        self.validation_and_error_check()

        # modify attributes based on self.form
        return self.sorting_func(request)

    def post(self, request, *args, **kwargs):
        ''' feed the post data in the form (up to obtain the cleaned data from post)'''
        # initialize the form list for setting default values
        self.forms = [None] * len(self.form_class)

        # loop for instantiating with data of POST request
        for counter, element_form_class in enumerate(self.form_class):
            self.forms[counter] = element_form_class(request.POST)

        self.validation_and_error_check()
        # modify attributes based on self.form
        return self.sorting_func(request)

    def validation_and_error_check(self):
        for element_forms in self.forms:  # for loop for making clean data by is_valid() method
            element_forms.is_valid()
            for errorField in element_forms.errors: # temporary error message
                print(f"errorField")

    def sorting_func(self, request):
        self.ds = CatalogDataset.objects.all()
        self.filtering_func()
        return self.final_rendering(request)


    def final_rendering(self, request):
        ''' Render page based on several forms of data as well as some other context '''
        self.set_context()
        return render(request, self.main_template, self.context)


# functions to be overloaded in child classes

    def filtering_func(self):
        # filter by source
        src=[]
        for element_forms in self.forms:
            if 'source' in element_forms.cleaned_data:
                if element_forms.cleaned_data['source'] is not None:
                    src.append(element_forms.cleaned_data['source'])

        self.ds = self.ds.filter(source__in=src)
        # filter by time
        t0 = self.forms[1].cleaned_data['time_coverage_start']
        t1 = self.forms[1].cleaned_data['time_coverage_end'] + timezone.timedelta(hours=24)
        self.ds = self.ds.filter(Q(time_coverage_end__lt=t1) & Q(time_coverage_start__gt=t0))
        # filter by geometry
        if self.forms[0].cleaned_data['polygon'] is not None:
            self.ds = self.ds.filter(geographic_location__geometry__intersects= self.forms[0].cleaned_data['polygon'])
        # ds = blabla(ds)
        #return self.ds

    def set_context(self):
        self.context = {}  # initializing the contect for templates
        # initializing the list of the forms that passed into context
        form_list = [None] * len(self.forms)
        for counter, value in enumerate(self.forms):
            # make the form_list elements one by one (form by form)
            form_list[counter] = value
        # passing the form_list into context
        self.context['form_list'] = form_list
        self.context['datasets'] = self.ds

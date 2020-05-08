from django.shortcuts import render
from django.utils import timezone
from django.views.generic import View
from geospaas.base_viewer.forms import SearchForm
from geospaas.base_viewer.forms import Search_with_para_Form
# Create your views here.
class IndexView(View):
    form_class = SearchForm
    main_template = 'base_viewer/template_for_base.html'
    viewname = 'index'
    form = None
    context = {}

    def set_form_defaults(self, request):
        ''' Set default values for the form '''
        self.form = self.form_class(
                    {'date0' :
                        timezone.datetime(2000,1,1,tzinfo=timezone.utc).date(),
                     'date1' : timezone.now().date()})

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        # set default values of form
        self.set_form_defaults(request)
        self.form.is_valid()

        # modify attributes based on self.form
        return self.render_func(request)

    def post(self, request, *args, **kwargs):
        ''' Render page is some data is given in the form '''
        # set default values of form

        # create new form from POST data
        form = self.form_class(request.POST)

        # replace erroneous data in the form with default values
        if not form.is_valid():
            for errorField in form.errors:
                form.cleaned_data[errorField] = self.form[errorField]

        # keep the query
        if form.is_valid():
            s = form.save(commit=False)
            s.sdate = timezone.now().date()
            s.save()

        # keep the form in self
        self.form = form
        self.form.is_valid()

        # modify attributes based on self.form
        return self.render_func(request)


    def render_func(self, request):
        ''' Render page based on form data '''
        # filter datasets
        #self.context['dsp'] = DatasetParameter
        #self.context['datasets'] = datasets

        self.context['formi'] = self.form
        return render(request, self.main_template, self.context)

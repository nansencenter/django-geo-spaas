import datetime
import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, FormMixin
from django.views.generic.list import ListView, MultipleObjectMixin

from nansencloud.viewer.models import Dataset
from nansencloud.viewer.forms import SearchForm

class DisplayForm(TemplateView):

    template_name = 'viewer/image_index.html' 

    def get_context_data(self, **kwargs):
        context = super(DisplayForm, self).get_context_data(**kwargs)
        context['form'] = SearchForm()
        # If we want to show some datasets by default, e.g., from the last few
        # days, we can load them here
        return context

class SearchDatasets(FormView):

    form_class = SearchForm
    template_name = 'viewer/image_index.html'
    success_url = reverse_lazy('index')

    def form_valid(self, *args, **kwargs):
        # This method is called when valid form data has been POSTed, so we can
        # store the search
        s = self.get_form().save(commit=False)
        s.sdate = datetime.datetime.today()
        s.save()
        return super(FormView, self).form_valid(*args, **kwargs)

# See
# https://docs.djangoproject.com/es/1.9/topics/class-based-views/mixins/#an-alternative-better-solution
class DatasetsShow(ListView):

    template_name = 'viewer/image_index.html' 
    model = Dataset
    paginate_by = 20

    def get(self, *args, **kwargs):
        view = DisplayForm.as_view()
        return view(*args, **kwargs)

    def post(self, *args, **kwargs):
        view = SearchDatasets.as_view()
        result = view(*args, **kwargs)
        form = result.context_data['form']
        import ipdb
        ipdb.set_trace()
        date0 = form.cleaned_data['date0']
        date1 = form.cleaned_data['date1']

        datasets = Dataset.objects.all()
        datasets = datasets.order_by('time_coverage_start')
        datasets = datasets.filter(time_coverage_start__gte=date0)
        datasets = datasets.filter(time_coverage_start__lte=date1)
        if form.cleaned_data['polygon'] is not None:
            datasets = datasets.filter(
                    geographic_location__geometry__intersects
                    = form.cleaned_data['polygon']
                )
        if form.cleaned_data['source'] is not None:
            datasets = datasets.filter(source=form.cleaned_data['source'])
        self.object_list = datasets

        return result
        
    ## The use of "image" here may be wrong - perhaps better to use "dataset"?
    #image_class = Dataset
    #main_template = 'viewer/image_index.html'
    #viewname = 'index'
    #form = None
    #context = {}

    #def set_form_defaults(self, request):
    #    ''' Set default values for the form '''
    #    self.form = self.form_class(
    #                {'date0' : datetime.date(2000,1,1),
    #                 'date1' : datetime.date.today()})

    #def set_params(self):
    #    ''' Set attributes based on form '''
    #    pass

    #def get(self, request, *args, **kwargs):
    #    ''' Render page if no data is given '''
    #    # set default values of form
    #    #self.set_form_defaults(request)
    #    import ipdb
    #    ipdb.set_trace()
    #    self.form.is_valid()

    #    # modify attributes based on self.form
    #    self.set_params()
    #    return self.render(request)

    #def post(self, request, *args, **kwargs):
    #    ''' Render page is some data is given in the form '''
    #    # set default values of form
    #    #self.set_form_defaults(request)

    #    # create new form from POST data
    #    form = self.form_class(request.POST)

    #    ## replace erroneous data in the form with default values
    #    #if not form.is_valid():
    #    #    for errorField in form.errors:
    #    #        form.cleaned_data[errorField] = self.form[errorField]

    #    # keep the query
    #    if form.is_valid():
    #        s = form.save(commit=False)
    #        s.sdate = datetime.datetime.today()
    #        s.save()

    #    ## keep the form in self
    #    #self.form = form
    #    #self.form.is_valid()

    #    ## modify attributes based on self.form
    #    #self.set_params()
    #    #return self.render(request)

    #def get_context_data(self, *args, **kwargs):
    #    context = super(IndexView, self).get_context_data(*args, **kwargs)

    #    ''' Render page based on form data '''
    #    # filter images
    #    # debuggin outuput
    #    greeting = ''
    #    #greeting += 'greet: ' + str(request.POST)
    #    #greeting += str(self.form.cleaned_data['sensor'])

    #    # paginating
    #    page = request.POST.get('page', 1)
    #    paginator = Paginator(images, 20)
    #    try:
    #        images = paginator.page(page)
    #    except PageNotAnInteger:
    #        # If page is not an integer, deliver first page.
    #        images = paginator.page(1)
    #    except EmptyPage:
    #        # If page is out of range (e.g. 9999), deliver last page of results.
    #        images = paginator.page(paginator.num_pages)

    #    context['images'] = images
    #    context['form'] = self.form
    #    context['greeting'] = greeting
    #    context['viewname'] = self.viewname

    #    return context
    #    #return render(request, self.main_template, self.context)

def image(request, image_id):
    image = Dataset.objects.get(id=image_id)
    context = {'image': image}#, 'info': image.info()}

    return render(request, 'viewer/image.html', context)

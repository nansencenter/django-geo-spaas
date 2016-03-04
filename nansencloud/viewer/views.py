import datetime
from dateutil.parser import parse

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

    def dispatch(self, *args, **kwargs):
        import ipdb
        ipdb.set_trace()
        return super(SearchDatasets, self).dispatch(*args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        import ipdb
        ipdb.set_trace()
        return super(SearchDatasets, self).get_template_names(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        import ipdb
        ipdb.set_trace()
        return super(SearchDatasets, self).get_context_data(*args, **kwargs)

    def from_invalid(self, *args, **kwargs):
        import ipdb
        ipdb.set_trace()
        return super(SearchDatasets, self).form_invalid(*args, **kwargs)

    def is_valid(self, *args, **kwargs):
        import ipdb
        ipdb.set_trace()
        return super(SearchDatasets, self).is_valid(*args, **kwargs)

    def save(self, *args, **kwargs):
        search = super(SearchDataset, self).save(*args, **kwargs)
        # Add date of search to the model instance
        search.sdate = datetime.datetime.today()
        search.save()
        return search

# See
# https://docs.djangoproject.com/es/1.9/topics/class-based-views/mixins/#an-alternative-better-solution
class DatasetsShow(ListView):

    form_class = SearchForm
    template_name = 'viewer/image_index.html'
    model = Dataset
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        view = DisplayForm.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            date0 = form.cleaned_data['date0']
            date1 = form.cleaned_data['date1']
            polygon = form.cleaned_data['polygon']
            source = form.cleaned_data['source']

        import ipdb
        ipdb.set_trace()

        datasets = Dataset.objects.all()
        datasets = datasets.order_by('time_coverage_start')
        datasets = datasets.filter(time_coverage_start__gte=date0)
        datasets = datasets.filter(time_coverage_start__lte=date1)
        if polygon is not None:
            datasets = datasets.filter(
                    geographic_location__geometry__intersects=polygon)
        if source is not None:
            datasets = datasets.filter(source=source)
        self.object_list = datasets

        view = SearchDatasets.as_view()
        return view(request, *args, **kwargs)


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

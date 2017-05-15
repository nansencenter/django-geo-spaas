from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View
from django.db.models import Q

#from geospaas.catalog.models import Dataset
from geospaas.viewer.models import Dataset, Visualization
from geospaas.viewer.forms import SearchForm

class IndexView(View):
    form_class = SearchForm
    image_class = Dataset
    main_template = 'viewer/dataset_index.html'
    viewname = 'index'
    form = None
    context = {}

    def set_form_defaults(self, request):
        ''' Set default values for the form '''
        self.form = self.form_class(
                    {'date0' :
                        timezone.datetime(2000,1,1,tzinfo=timezone.utc).date(),
                     'date1' : timezone.now().date()})

    def set_params(self):
        ''' Set attributes based on form '''
        pass

    def get(self, request, *args, **kwargs):
        ''' Render page if no data is given '''
        # set default values of form
        self.set_form_defaults(request)
        self.form.is_valid()

        # modify attributes based on self.form
        self.set_params()
        return self.render(request)

    def post(self, request, *args, **kwargs):
        ''' Render page is some data is given in the form '''
        # set default values of form
        self.set_form_defaults(request)

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
        self.set_params()
        return self.render(request)

    def render(self, request):
        ''' Render page based on form data '''
        # filter datasets
        datasets = self.image_class.objects.all()
        datasets = datasets.order_by('time_coverage_start')
        if self.form.cleaned_data['source'] is not None:
            src = self.form.cleaned_data['source']
            datasets = datasets.filter(source__in=src)
        t0 = self.form.cleaned_data['date0']
        t1 = self.form.cleaned_data['date1'] + timezone.timedelta(hours=24)
        datasets = datasets.filter(
                #Q(time_coverage_start__range=[t0,t1]) |
                #Q(time_coverage_end__range=[t0,t1]) |
                #(
                Q(time_coverage_start__lt=t1) & Q(time_coverage_end__gt=t0)
                #)
            )
        if self.form.cleaned_data['polygon'] is not None:
            datasets = datasets.filter(
                    geographic_location__geometry__intersects
                    = self.form.cleaned_data['polygon']
                )
        #if self.form.cleaned_data['collocate_with'] is not None:
        #    src = self.form.cleaned_data['collocate_with']

        # debuggin outuput
        greeting = ''
        #greeting += 'greet: ' + str(request.POST)
        #greeting += str(self.form.cleaned_data['sensor'])

        # paginating
        page = request.POST.get('page', 1)
        paginator = Paginator(datasets, 10)
        try:
            datasets = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            datasets = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            datasets = paginator.page(paginator.num_pages)

        params = []
        for dataset in datasets:
            visualizations = dataset.visualizations()
            for viz in visualizations:
                for ds_parameter in viz.ds_parameters.all():
                    if not ds_parameter.parameter.standard_name in params:
                        params.append(ds_parameter.parameter.standard_name)

        visualizations = {}
        for pp in params:
            visualizations[pp] = []
            for ds in datasets:
                visualizations[pp].extend(Visualization.objects.filter(
                    ds_parameters__parameter__standard_name=pp,
                    ds_parameters__dataset=ds))

        self.context['params'] = params
        self.context['visualizations'] = visualizations
        self.context['datasets'] = datasets
        self.context['form'] = self.form
        self.context['greeting'] = greeting
        self.context['viewname'] = self.viewname
        return render(request, self.main_template, self.context)

def dataset(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    context = {'dataset': dataset}#, 'info': dataset.info()}

    return render(request, 'viewer/dataset.html', context)

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View

#from nansencloud.catalog.models import Dataset
from nansencloud.viewer.models import Dataset, Visualization
from nansencloud.viewer.forms import SearchForm

class IndexView(View):
    form_class = SearchForm
    image_class = Dataset
    main_template = 'viewer/image_index.html'
    viewname = 'index'
    form = None
    context = {}

    def set_form_defaults(self, request):
        ''' Set default values for the form '''
        self.form = self.form_class(
                    {'date0' : timezone.datetime(2000,1,1,tzinfo=timezone.utc).date(),
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
        # filter images
        images = self.image_class.objects.all()
        images = images.order_by('time_coverage_start')
        images = images.filter(time_coverage_start__gte=self.form.cleaned_data['date0'])
        images = images.filter(time_coverage_start__lte=self.form.cleaned_data['date1'])
        if self.form.cleaned_data['polygon'] is not None:
            images = images.filter(
                    geographic_location__geometry__intersects
                    = self.form.cleaned_data['polygon']
                )
        if self.form.cleaned_data['source'] is not None:
            images = images.filter(source=self.form.cleaned_data['source'])

        params = []
        for image in images:
            visualizations = image.visualizations()
            for viz in visualizations:
                for ds_parameter in viz.ds_parameters.all():
                    if not ds_parameter.parameter.standard_name in params:
                        params.append(ds_parameter.parameter.standard_name)

        visualizations = {}
        for pp in params:
            visualizations[pp] = []
            for ds in images:
                visualizations[pp].extend(Visualization.objects.filter(
                    ds_parameters__parameter__standard_name=pp,
                    ds_parameters__dataset=ds))

        # debuggin outuput
        greeting = ''
        #greeting += 'greet: ' + str(request.POST)
        #greeting += str(self.form.cleaned_data['sensor'])

        # paginating
        page = request.POST.get('page', 1)
        paginator = Paginator(images, 20)
        try:
            images = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            images = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            images = paginator.page(paginator.num_pages)

        self.context['params'] = params
        self.context['visualizations'] = visualizations
        self.context['images'] = images
        self.context['form'] = self.form
        self.context['greeting'] = greeting
        self.context['viewname'] = self.viewname
        return render(request, self.main_template, self.context)

def image(request, image_id):
    image = Dataset.objects.get(id=image_id)
    context = {'image': image}#, 'info': image.info()}

    return render(request, 'viewer/image.html', context)

import datetime
import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View

from nansatcat.models import Image
from nansatcat.forms import SearchForm

class IndexView(View):
    form_class = SearchForm
    image_class = Image
    main_template = 'nansatcat/image_index.html'
    viewname = 'index'
    form = None
    context = {}

    def set_form_defaults(self, request):
        ''' Set default values for the form '''
        self.form = self.form_class(
                    {'date0' : datetime.date(2000,1,1),
                     'date1' : datetime.date.today()})

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
            s.sdate = datetime.datetime.today()
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
        images = images.order_by('start_date')
        images = images.filter(start_date__gte=self.form.cleaned_data['date0'])
        images = images.filter(start_date__lte=self.form.cleaned_data['date1'])
        if self.form.cleaned_data['polygon'] is not None:
            images = images.filter(border__intersects=self.form.cleaned_data['polygon'])
        if self.form.cleaned_data['status'] is not None:
            images = images.filter(status=self.form.cleaned_data['status'])
        if self.form.cleaned_data['sensor'] is not None:
            images = images.filter(sensor=self.form.cleaned_data['sensor'])
        if self.form.cleaned_data['satellite'] is not None:
            images = images.filter(satellite=self.form.cleaned_data['satellite'])

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

        self.context['images'] = images
        self.context['form'] = self.form
        self.context['greeting'] = greeting
        self.context['viewname'] = self.viewname
        return render(request, self.main_template, self.context)

def image(request, image_id):
    image = Image.objects.get(id=image_id)
    context = {'image': image}#, 'info': image.info()}

    return render(request, 'nansatcat/image.html', context)

def band(request, image_id, bandName):
    image = Image.objects.get(id=image_id)
    band = image.bands.get(id=bandName)

    img = band.get_image()
    response = HttpResponse(content_type="image/jpeg")
    img.save(response, "PNG")
    return response

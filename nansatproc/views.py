import datetime

from django.shortcuts import render, render_to_response
from django.template.context import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from nansatcat.models import Image
from nansatcat.views import IndexView

from nansatproc.forms import ProcSearchForm
from nansatproc.models import *


class ProcIndexView(IndexView):
    form_class = ProcSearchForm
    viewname = 'proc_index'
    main_template = 'nansatcat/image_index.html'

    def set_params(self):
        ''' Set default values for the form '''
        chain = self.form.cleaned_data['chain']
        if chain is None:
            self.image_class = Image
            self.context['chain_id'] = 0
            self.main_template = 'nansatcat/image_index.html'
        else:
            self.image_class = eval(chain.name)
            self.context['chain_id']=chain.id
            self.main_template = 'nansatproc/%s_index.html' % chain.name.lower()

def proc_image(request, chain_id, image_id):

    try:
        chain = Chain.objects.get(id=chain_id)
        theTable = eval(chain.name)
        template = 'nansatproc/%s_image.html' % chain.name.lower()
    except:
        theTable = Image
        template = 'nansatcat/image.html'

    image = theTable.objects.get(id=image_id)
    doy = image.start_date.timetuple().tm_yday
    if doy<100:
        if doy<10:
            doy = '00'+str(doy)
        else:
            doy = '0'+str(doy)
    else:
        doy = str(doy)
    if abs(image.border.centroid.coords[1]>60):
        min_sst = 271
        max_sst = 295
    elif abs(image.border.centroid.coords[1]>30) and \
            abs(image.border.centroid.coords[1]<=60):
        min_sst = 281
        max_sst = 300
    else:
        min_sst = 291
        max_sst = 310
    context = {
            'image': image,
            'year': image.start_date.year,
            'doy': doy,
            'datestr': image.start_date.strftime('%Y%m%d'),
            'max_sst': max_sst - 273,
            'min_sst': min_sst - 273,
            'center': '['+ str(image.border.centroid.coords[1])
                        +','+ str(image.border.centroid.coords[0]) + ']',
        }

    return render_to_response(template,
            context_instance=RequestContext(request, context))

def matchup(request, chain_id, image_id):

    dateHalfWindow = 2 # days

    try:
        chain = Chain.objects.get(id=chain_id)
        theTable = eval(chain.name)
        template = 'nansatproc/%s_images.html' % chain.name.lower()
    except:
        theTable = Image
        template = 'nansatproc/images.html'

    image = theTable.objects.get(id=image_id)
    images = theTable.objects.filter(border__intersects=image.border)
    images = images.filter(start_date__gte=(image.start_date - datetime.timedelta(dateHalfWindow)))
    images = images.filter(stop_date__lte=(image.stop_date + datetime.timedelta(dateHalfWindow)))

    quicklooks = []
    for image in images:
        for ql in image.quicklooks.all():
            quicklooks.append(ql)
    context = {'quicklooks': quicklooks}


    return render_to_response(template,
            context_instance=RequestContext(request, context))

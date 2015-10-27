from django.shortcuts import render

from nansencloud.catalog.models import Dataset, DataLocation


# Create your views here.
from django.http import HttpResponse


def index(request):
    uris = sorted(list(DataLocation.objects.filter(dataset__time_coverage_start__gte='1200-01-01').values_list('uri', flat=True)))
    times = sorted(list(DataLocation.objects.filter(dataset__time_coverage_start__gte='1200-01-01').values_list('dataset__time_coverage_start', flat=True)))

    output = '\n'.join(['<li>%s at %s</li>' % (uri, time) for uri, time in zip(uris, times)])
    return HttpResponse(output)

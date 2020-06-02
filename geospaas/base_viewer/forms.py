from django.contrib.gis import forms
from django.db.models import Q
from django.forms import CharField
from django.utils import timezone
from leaflet.forms.widgets import LeafletWidget

from geospaas.catalog.models import Source


class OverallForm(forms.Form):

    polygon = forms.GeometryField(label='choose a location (or leave it empty for all locations)',
                                  widget=LeafletWidget(attrs={
                                      'settings_overrides': {
                                          'DEFAULT_CENTER': (60.0, 5.0),
                                          'DEFAULT_ZOOM': 1,
                                          'PLUGINS': {'forms': {'auto-include': True}},
                                      }
                                  }))
    time_coverage_start = forms.DateTimeField(
        initial=timezone.datetime(2000, 1, 1))
    time_coverage_end = forms.DateTimeField(initial=timezone.now())
    source = forms.ModelChoiceField(
        Source.objects.all(), required=False)

    def filter(self, ds):
        # filtering based on time
        t0 = self.cleaned_data['time_coverage_start']
        t1 = self.cleaned_data['time_coverage_end'] + \
            timezone.timedelta(hours=24)
        ds = ds.filter(Q(time_coverage_end__lt=t1) &
                       Q(time_coverage_start__gt=t0))

        # filtering based on source

        src = [self.cleaned_data['source']]
        ds = ds.filter(source__in=src)

        # spatial filtering
        if 'polygon' in self.cleaned_data:
            ds = ds.filter(
                geographic_location__geometry__intersects=self.cleaned_data['polygon'])
        return ds

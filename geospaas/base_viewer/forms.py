from django.contrib.gis import forms
from django.utils import timezone
from leaflet.forms.widgets import LeafletWidget

from geospaas.catalog.models import Source


class BaseSearchForm(forms.Form):
    """ Basic version of form for basic seaching of django-geospaas metadata """
    polygon = forms.GeometryField(label=False,
                                  widget=LeafletWidget(attrs={
                                      'settings_overrides': {
                                          'DEFAULT_CENTER': (60.0, 5.0),
                                          'DEFAULT_ZOOM': 1,
                                          'PLUGINS': {'forms': {'auto-include': True}},
                                      }
                                  }),
                                  required=False)
    time_coverage_start = forms.DateTimeField(
        initial=timezone.datetime(2000, 1, 1, tzinfo=timezone.utc))
    time_coverage_end = forms.DateTimeField(initial=timezone.now())
    source = forms.ModelMultipleChoiceField(
        Source.objects.all(), required=False)

    def filter(self, ds):
        """ Filtering method of the form. All filtering processes are coded here """
        # filtering based on time
        t_0 = self.cleaned_data['time_coverage_start']
        t_1 = self.cleaned_data['time_coverage_end']
        # Too early datasets are excluded from the filtering results
        ds = ds.exclude(time_coverage_end__lt=t_0)

        # Too late datasets are excluded from the filtering results
        ds = ds.exclude(time_coverage_start__gt=t_1)

        src = self.cleaned_data.get('source', None)
        # Just the one(s) with correct selected source should pass the filtering actions
        # if Source is given in the input form
        if src:
            ds = ds.filter(source__in=src)

        # spatial filtering
        if self.cleaned_data['polygon']:
            # filtering by user provided polygon
            ds = ds.filter(
                geographic_location__geometry__intersects=self.cleaned_data['polygon'])

        # sorting
        ds = ds.order_by('time_coverage_start')
        return ds

from django.contrib.gis import forms
from django.db.models import Q
from django.utils import timezone
from leaflet.forms.widgets import LeafletWidget

from geospaas.base_viewer.models import SearchModelForLeaflet
from geospaas.catalog.models import Dataset as CatalogDataset

#from geospaas.base_viewer.models import Search_with_para

class BaseForm(forms.ModelForm):
    initial = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(initial=self.initial, *args, **kwargs)


class TimeAndSourceForm(BaseForm):
    initial = dict(
        time_coverage_end = timezone.now(),
        time_coverage_start = timezone.datetime(2000, 1, 1),
        )
    class Meta:
        model = CatalogDataset
        fields = ['time_coverage_start', 'time_coverage_end', 'source']

    #def set_defaults(self):
    #    self.data['time_coverage_end'] = timezone.now()
    #    self.data['time_coverage_start'] = timezone.datetime(2000, 1, 1,
    #                                                         tzinfo=timezone.utc).date()
    #    self.data['source'] = CatalogDataset.objects.first().source

    def filter(self, ds):
        t0 = self.cleaned_data['time_coverage_start']
        t1 = self.cleaned_data['time_coverage_end'] + \
            timezone.timedelta(hours=24)
        ds = ds.filter(Q(time_coverage_end__lt=t1) &
                       Q(time_coverage_start__gt=t0))
        src = [self.cleaned_data['source']]
        ds = ds.filter(source__in=src)
        return ds


class SpatialSearchForm(BaseForm):
    #initial = None
    class Meta:
        model = SearchModelForLeaflet
        fields = ['polygon']
        labels = {
            'polygon': 'Draw your polygon (or leave it empty for all locations)'}
        widgets = {'polygon': LeafletWidget(
            attrs={'settings_overrides':
                   {'DEFAULT_CENTER': (60.0, 5.0),
                    'DEFAULT_ZOOM': 1,
                    'PLUGINS': {'forms': {'auto-include': True}},
                    }}
        )}

    #def set_defaults(self):
    #    pass

    def filter(self, ds):
        received_polygon = self.cleaned_data['polygon']
        if received_polygon is not None:
            ds = ds.filter(
                geographic_location__geometry__intersects=received_polygon)
        return ds


# class Search_with_para_Form(SearchForm_below):
#   fields = SearchForm.Meta.fields.append('DatasetParameter')

    # def __init__(self, *args, **kwargs):
    ####    super().__init__( *args, **kwargs)

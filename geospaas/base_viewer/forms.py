from django.contrib.gis import forms
from django.utils import timezone
from django.db.models import Q

from leaflet.forms.widgets import LeafletWidget
from geospaas.catalog.models import Dataset as CatalogDataset
from django.contrib.gis.db import models as geomodels

from geospaas.base_viewer.models import Search_dummy_leaflet
#from geospaas.base_viewer.models import Search_with_para
class SearchFormBelow(forms.ModelForm):
    class Meta:
        model = CatalogDataset
        fields = ['time_coverage_start','time_coverage_end','source']

    def set_defaults(self):
        self.data['time_coverage_end'] = timezone.now().date()
        self.data['time_coverage_start'] = timezone.datetime(2000, 1, 1,
                    tzinfo=timezone.utc).date()
        self.data['source'] = CatalogDataset.objects.first().source

    def filter(self,ds):
        t0 = self.cleaned_data['time_coverage_start']
        t1 = self.cleaned_data['time_coverage_end'] + timezone.timedelta(hours=24)
        ds = ds.filter(Q(time_coverage_end__lt=t1) & Q(time_coverage_start__gt=t0))
        src=[]
        src.append(self.cleaned_data['source'])
        ds = ds.filter(source__in=src)
        return ds

class SearchFormAbove(forms.ModelForm):
    class Meta:
        model = Search_dummy_leaflet
        fields = ['polygon']
        labels = {'polygon':'Draw your polygon (or leave it empty for all locations)'}
        widgets = {'polygon': LeafletWidget(
                attrs={'settings_overrides':
                        {'DEFAULT_CENTER': (60.0, 5.0),
                        'DEFAULT_ZOOM': 1,
                        'PLUGINS': {'forms': {'auto-include': True}},
                         }}
                        )}
    def set_defaults(self):
        pass

    def filter(self,ds):
        received_polygon= self.cleaned_data['polygon']
        if received_polygon is not None:
            ds = ds.filter(geographic_location__geometry__intersects= received_polygon)
            return ds
        else:
            # in the case that user have no specified polygon
            # there is no need to filter
            return ds

#class Search_with_para_Form(SearchForm_below):
#   fields = SearchForm.Meta.fields.append('DatasetParameter')

    ####def __init__(self, *args, **kwargs):
    ####    super().__init__( *args, **kwargs)

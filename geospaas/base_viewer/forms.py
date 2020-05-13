from django.contrib.gis import forms
from django.utils import timezone
from leaflet.forms.widgets import LeafletWidget
from geospaas.catalog.models import Dataset as CatalogDataset
from django.contrib.gis.db import models as geomodels

from geospaas.base_viewer.models import Search_dummy_leaflet
#from geospaas.base_viewer.models import Search_with_para
class SearchFormBelow(forms.ModelForm):
    class Meta:

        model = CatalogDataset
        fields = ['time_coverage_start','time_coverage_end','source']

    def __init__(self, *args, **kwargs):
        #self.geographic_location = CatalogGeographicLocation
        initial = kwargs.pop('initial', {})
        initial['time_coverage_start'] = timezone.datetime(2000, 1, 1,
                    tzinfo=timezone.utc).date(),
        initial['time_coverage_end'] = timezone.now().date()
        initial['source'] = CatalogDataset.objects.first().source
        super().__init__(initial=initial, *args, **kwargs)


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

#class Search_with_para_Form(SearchForm_below):
#   fields = SearchForm.Meta.fields.append('DatasetParameter')

    ####def __init__(self, *args, **kwargs):
    ####    super().__init__( *args, **kwargs)

from django.contrib.gis import forms
from django.utils import timezone
from leaflet.forms.widgets import LeafletWidget

from geospaas.base_viewer.models import Search
from geospaas.base_viewer.models import Search_with_para
class SearchForm(forms.ModelForm):

    class Meta:

        model = Search
        #fields = ['polygon', 'date0', 'date1', 'source']
        fields = '__all__'
        exclude = ('sdate',)
        widgets = {'polygon': LeafletWidget(
                attrs={    'map_height': '500px',
                            'map_width': '100%',
                            'display_raw': 'true',
                            'map_srid': 4326,},
                        ),
                   'date0': forms.DateInput(attrs={'class':'datepicker'}),
                   'date1': forms.DateInput(attrs={'class':'datepicker'}),}

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        initial['date0'] = timezone.datetime(2000, 1, 1,
                    tzinfo=timezone.utc).date(),
        initial['date1'] = timezone.now().date()
        super().__init__(initial=initial, *args, **kwargs)

class Search_with_para_Form(SearchForm):

    class Meta(SearchForm.Meta):
        model = Search_with_para

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

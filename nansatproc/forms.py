from django.contrib.gis import forms

from leaflet.forms.widgets import LeafletWidget

from nansatcat.forms import SearchForm
from nansatproc.models import ProcSearch

class ProcSearchForm(forms.ModelForm):

    class Meta(SearchForm.Meta):
        model = ProcSearch
        fields = SearchForm.Meta.fields + ['chain']

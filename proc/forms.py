from django.contrib.gis import forms

from leaflet.forms.widgets import LeafletWidget

from cat.forms import SearchForm
from proc.models import ProcSearch

class ProcSearchForm(forms.ModelForm):

    class Meta(SearchForm.Meta):
        model = ProcSearch
        fields = SearchForm.Meta.fields + ['chain']

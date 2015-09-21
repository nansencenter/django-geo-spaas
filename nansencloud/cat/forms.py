from django.contrib.gis import forms

from nansencloud.cat.models import Search

from leaflet.forms.widgets import LeafletWidget


class SearchForm(forms.ModelForm):

    class Meta:
        model = Search
        fields = ['polygon', 'date0', 'date1', 'status', 'sensor', 'satellite']
        labels = {'polygon':''}
        widgets = {'polygon': LeafletWidget(),
                   'date0': forms.DateInput(attrs={'class':'datepicker'}),
                   'date1': forms.DateInput(attrs={'class':'datepicker'}),}

from mock.mock import MagicMock, patch, create_autospec

from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Polygon, LinearRing

from nansencloud.catalog.models import Source
from nansencloud.viewer import forms
from nansencloud.viewer.models import Search
from nansencloud.viewer.models import Dataset
from nansencloud.viewer.models import Visualization
from nansencloud.viewer.models import VisualizationParameter

class FormTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_search_form(self):
        ext_coords = ((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))
        #int_coords = ((0.4, 0.4), (0.4, 0.6), (0.6, 0.6), (0.6, 0.4), (0.4,
        #    0.4))
        #poly = Polygon(ext_coords, int_coords)
        poly = Polygon(LinearRing(ext_coords))
        date0 = '2010-01-01', #timezone.datetime(2010,1,1, tzinfo=timezone.utc)
        date1 = '2011-01-01', #timezone.datetime(2011,1,1, tzinfo=timezone.utc)
        source = Source.objects.get(pk=1)
        test_search = {
                'polygon': poly,
                'date0': date0, 
                'date1': date1,
                'source': source
            }
        form = forms.SearchForm(data=test_search)
        self.failUnless(form.is_valid())

class ModelTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def test_search_model(self):
        sdate = timezone.datetime(2016,1,1,tzinfo=timezone.utc)
        date0 = timezone.datetime(2010,1,1,tzinfo=timezone.utc)
        date1 = timezone.datetime(2010,1,2,tzinfo=timezone.utc)
        source = Source.objects.get(pk=1)
        ext_coords = ((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))
        polygon = Polygon(LinearRing(ext_coords))
        
        search = Search(sdate=sdate, date0=date0, date1=date1, source=source,
                polygon=polygon)
        search.save()
        self.assertEqual(search.date0, date0)

    def test_dataset_model(self):
        pass

    def test_visualization_model(self):
        pass

    def test_visualization_parameter_model(self):
        pass

class ViewTests(TestCase):

    def test_call_index_view_loads(self):
        pass

    def test_call_index_view_blank_form(self):
        pass

    def test_call_index_view_invalid_form(self):
        pass

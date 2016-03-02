from mock.mock import MagicMock, patch, create_autospec

from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Polygon, LinearRing

from nansencloud.vocabularies.models import Parameter
from nansencloud.catalog.models import Source
from nansencloud.catalog.models import DatasetParameter
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

    def setUp(self):
        self.ds = Dataset.objects.get(pk=1)

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
        self.assertIsInstance(search.__str__(), str)

    def test_dataset_geojs(self):
        self.assertIsInstance(self.ds.geo_js(), str)

    def test_dataset_const_geojs(self):
        self.assertIsInstance(self.ds.const_geo_js(), str)

    def test_dataset_border2str(self):
        self.assertIsInstance(self.ds.border2str(), str)

    #@patch(Visualization.objects, 'filter')
    #def test_dataset_visualizations(self, visfilter_mock):
    #    vv = self.ds.visualizations()
    #    visfilter_mock.assert_called_once_with(self.ds)

    def test_dataset_visualizations_not_mocked(self):
        sigma0 = Parameter.objects.get(short_name='sigma0')
        wind = Parameter.objects.get(standard_name='wind_speed')
        dp0 = DatasetParameter(dataset=self.ds, parameter=sigma0)
        dp0.save()
        dp1 = DatasetParameter(dataset=self.ds, parameter=wind)
        dp1.save()
        uri = 'file://localhost/this/is/a/png/file.png'
        v = Visualization(uri=uri)
        v.save()
        visparam0 = VisualizationParameter(visualization=v, ds_parameter=dp0)
        visparam0.save()
        visparam1 = VisualizationParameter(visualization=v, ds_parameter=dp1)
        visparam1.save()

        self.assertEqual(len(self.ds.visualizations()), 1)

    def test_visualization_model(self):
        uri = 'file://localhost/this/is/a/png/file.png'
        title = 'This is a test visualization'
        v = Visualization(uri=uri, title=title)
        v.save()
        self.assertEqual(v.uri, uri)
        self.assertEqual(v.__str__(), title)
        self.assertIsInstance(v.__str__(), str)

    def test_visualization_parameter_model(self):
        sigma0 = Parameter.objects.get(short_name='sigma0')
        dp0 = DatasetParameter(dataset=self.ds, parameter=sigma0)
        dp0.save()
        uri = 'file://localhost/this/is/a/png/file.png'
        v = Visualization(uri=uri)
        v.save()
        visparam0 = VisualizationParameter(visualization=v, ds_parameter=dp0)
        visparam0.save()
        self.assertEqual(visparam0.ds_parameter.dataset.pk, self.ds.pk)
        self.assertIsInstance(visparam0.__str__(), str)

class ViewTests(TestCase):

    def test_call_index_view_loads(self):
        raise NotImplementedError

    def test_call_index_view_blank_form(self):
        raise NotImplementedError

    def test_call_index_view_invalid_form(self):
        raise NotImplementedError

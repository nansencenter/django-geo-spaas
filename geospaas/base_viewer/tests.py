from django.test import TestCase
from django.test import Client
import json
from mock import DEFAULT, MagicMock, Mock, PropertyMock, patch
from geospaas.base_viewer.views import IndexView
from geospaas.base_viewer.forms import TimeAndSourceForm, SpatialSearchForm

# Create your tests here.
#class GUIHavingNewBaseTests(TestCase):
#    fixtures = ["vocabularies", "catalog"]

    #def setUp(self):
    #    self.client = Client()
#
    #def test_the_get_verb_of_GUI(self):
#
    #    res = self.client.get('')
    #    #print(json.loads(res.content))
    #    self.assertEqual(res.status_code, 200)

class FunctionTestingForViews(TestCase):
    fixtures = ["vocabularies", "catalog"]


    def setUp(self):
        pass
        #self.client = Client()

    def test_creating_the_forms(self):
        #res = self.client.get('')
        v1 = IndexView()
        #self.assert('polygon' in v1.forms.__str__())
        self.assertFalse('polygon' in v1.forms.__str__())
        self.assertFalse('time_coverage_start' in v1.forms.__str__())
        self.assertFalse('time_coverage_end' in v1.forms.__str__())
        self.assertFalse('source' in v1.forms.__str__())
        v1.create_forms(self)
        self.assertTrue('polygon' in v1.forms.__str__())
        self.assertTrue('time_coverage_start' in v1.forms.__str__())
        self.assertTrue('time_coverage_end' in v1.forms.__str__())
        self.assertTrue('source' in v1.forms.__str__())
#############################
        #self.assertEqual(res.content, 200)
    #@patch('geospaas.base_viewer.IndexView.create_forms')
    #def test_order_of_forms(self, mock_mkdir):
    #    mock_mkdir
###############################
    def test_getting_all_datasets(self):
        v1 = IndexView()
        v1.create_forms(self)
        b = v1.get_all_datasets()
        self.assertEqual(len(b) , 2)
        self.assertEqual(b[1].__str__(),'AQUA/MODIS/2010-01-02T00:00:00+00:00')

    def test_setting_the_context(self):
        #res = self.client.get('')
        v1 = IndexView()
        v1.create_forms(self)
        v1.ds = v1.get_all_datasets()
        b = v1.get_all_datasets()
        v1.set_context()
        self.assertEqual(v1.context['datasets'][1].__str__(), b[1].__str__())

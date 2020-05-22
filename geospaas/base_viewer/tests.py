from html.parser import HTMLParser

from django.test import Client, TestCase
from django.utils import timezone

from geospaas.base_viewer.views import IndexView


class MyHTMLParser(HTMLParser):
    def __init__(self):
        """Constructor with extra attribute definition"""
        super().__init__()
        self.flag = False
        self.data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'td':  # find out the tags with td tags
            for attr in attrs:
                # find out the ones with ///class="place_ds"///
                if ('class' in attr) and ('place_ds' in attr):
                    self.flag = True # make the flag true to enable the storage action

    def handle_data(self, Data):
        if (self.flag == True):# just store the data of specified tags with the help of flag
            self.data.append(Data)
            self.flag = False # make it false AGAIN in order not to save the data from other tags of HTML


class GUIHavingNewBaseIntegrationTests(TestCase):
    '''INtegration tests for GET and POST methods'''
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.client = Client()
        # this parser is configured to store the desired data of td tag into self.data
        self.parser = MyHTMLParser()

    def test_the_post_verb_of_GUI_with_proper_polygon(self):
        """shall return only the first dataset of fixtures in the specified placement of datasets inside the resulted HTML
        in the case of a POST request with a good choice of polygon"""
        res1 = self.client.post('/', {'polygon': '{"type":"Polygon","coordinates":[[[0,0],[0,5],[5,5],[5,0],[0,0]]]}',
                                      'time_coverage_start': timezone.datetime(2000, 12, 29),
                                      'time_coverage_end': timezone.datetime(2020, 1, 1),
                                      'source': 1})
        self.assertEqual(res1.status_code, 200)
        self.parser.feed(str(res1.content))
        # the first dataset of fixtures must be in the html
        self.assertIn(True, [('file://localhost/some/test/file1.ext' in dat)
                             for dat in self.parser.data])
        # the second dataset of fixturesshould not be in the html
        self.assertIn(False, [('file://localhost/some/test/file2.ext' in dat)
                              for dat in self.parser.data])

    def test_the_post_verb_of_GUI_with_nonrelevant_polygon(self):
        """shall return 'No datasets are...' in the specified placement of datasets inside the resulted HTML
        in the case of a POST request with nonrelevant polygon apart from the polygon of databases datasets"""
        res2 = self.client.post('/', {'polygon': '{"type":"Polygon","coordinates":[[[53.132629,-13.557892],[53.132629,4.346411],[73.721008,4.346411],[73.721008,-13.557892],[53.132629,-13.557892]]]}',
                                      'time_coverage_start': timezone.datetime(2000, 12, 29),
                                      'time_coverage_end': timezone.datetime(2020, 1, 1),
                                      'source': 1})
        self.assertEqual(res2.status_code, 200)
        self.parser.feed(str(res2.content))
        self.assertIn(True, [
                      ('No datasets are available (or maybe no one is ingested)' in dat) for dat in self.parser.data])

    def test_the_post_verb_of_GUI_without_polygon(self):
        """shall return the uri of fixtures' datasets in the specified placement of datasets inside the resulted HTML
        in the case of a POST request without any polygon from user """
        res3 = self.client.post('/', {
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'source': 1})
        self.assertEqual(res3.status_code, 200)
        self.parser.feed(str(res3.content))
        # both datasets must be in the html
        self.assertIn(True, [('file://localhost/some/test/file1.ext' in dat)
                             for dat in self.parser.data])
        self.assertIn(True, [('file://localhost/some/test/file2.ext' in dat)
                             for dat in self.parser.data])

    def test_the_post_verb_of_GUI_incorrect_dates_without_polygon(self):
        """shall return 'No datasets are...' in the specified placement of datasets inside the resulted HTML
        in the case of a POST request with incorrect dates from user and without any polygon from user"""
        res3 = self.client.post('/', {
            'time_coverage_start': timezone.datetime(2019, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'source': 1})
        self.assertEqual(res3.status_code, 200)
        self.parser.feed(str(res3.content))
        self.assertIn(True, [
                      ('No datasets are available (or maybe no one is ingested)' in dat) for dat in self.parser.data])

    def test_the_get_verb_of_GUI(self):
        """shall return ALL uri of fixtures' datasets in the specified placement
        of datasets inside the resulted HTML in the case of a GET request"""
        res4 = self.client.get('/')
        self.assertEqual(res4.status_code, 200)
        self.parser.feed(str(res4.content))
        # both datasets must be in the html
        self.assertIn(True, [('file://localhost/some/test/file1.ext' in dat)
                             for dat in self.parser.data])
        self.assertIn(True, [('file://localhost/some/test/file2.ext' in dat)
                             for dat in self.parser.data])


class UnitTestingForViews(TestCase):
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.v1 = IndexView()
        self.ds = self.v1.get_all_datasets()
        self.forms = self.v1.create_forms(self)

    def test_creating_the_forms(self):
        '''shall create the specified fields of forms'''
        self.assertTrue('polygon' in self.forms.__str__())
        self.assertTrue('time_coverage_start' in self.forms.__str__())
        self.assertTrue('time_coverage_end' in self.forms.__str__())
        self.assertTrue('source' in self.forms.__str__())

    def test_setting_the_context_correctly(self):
        '''shall return the correct key of context dictionary for correct viewing by templates'''
        context = self.v1.set_context(self.forms, self.ds)
        self.assertIn('TimeAndSourceForm', context.keys())
        self.assertIn('SpatialSearchForm', context.keys())
        self.assertIn('datasets', context.keys())

    def test_get_filtered_datasets(self):
        '''shall return the fixture datasets when large time-interval is set and none of them when a nonrelevant one is set'''
        forms = self.v1.create_forms({'polygon': '',
                                      'time_coverage_start': timezone.datetime(2000, 12, 29),
                                      'time_coverage_end': timezone.datetime(2020, 1, 1),
                                      'source': 1})
        forms = self.v1.validate_forms(forms)
        ds = self.v1.get_filtered_datasets(forms)
        self.assertEqual(len(ds), 2)  # shall return the fixture datasets
        self.assertEqual(
            '<QuerySet [<Dataset: AQUA/MODIS/2010-01-01T00:00:00+00:00>, <Dataset: AQUA/MODIS/2010-01-02T00:00:00+00:00>]>', str(ds))
        forms = self.v1.create_forms({'polygon': '',
                                      'time_coverage_start': timezone.datetime(2019, 12, 29),
                                      'time_coverage_end': timezone.datetime(2020, 1, 1),
                                      'source': 1})
        forms = self.v1.validate_forms(forms)
        ds = self.v1.get_filtered_datasets(forms)
        self.assertEqual(len(ds), 0)  # shall return no datasets

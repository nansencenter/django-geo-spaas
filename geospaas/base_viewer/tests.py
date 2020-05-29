from html.parser import HTMLParser

from django.test import Client, TestCase
from django.utils import timezone
from mock.mock import MagicMock, patch

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


class IntegrationTestsForGUIWithNewBase(TestCase):
    '''INtegration tests for GET and POST methods of GUI'''
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

class IndexViewTests(TestCase):
    @patch('geospaas.base_viewer.views.CatalogDataset')
    def test_get_all_datasets(self, mock_dataset):
        """ Shall call CatalogDataset.objects.all() inside get_all_datasets """
        IndexView.get_all_datasets()
        mock_dataset.objects.all.assert_called_once()

    def test_get_filtered_datasets(self):
        """ Shall  call filter function from form class once """
        form = MagicMock()
        ds = IndexView.get_filtered_datasets(form)
        form.filter.assert_called_once()#form.filter.

    def test_set_context(self):
        """ Shall  contain 'OverallForm' and 'datasets' in the context.
        Results should not be filtered by this function """
        form = MagicMock()
        ds = MagicMock()
        context = IndexView.set_context(form,ds)
        form.filter.assert_not_called()
        self.assertTrue('OverallForm' in context)
        self.assertTrue('datasets' in context)

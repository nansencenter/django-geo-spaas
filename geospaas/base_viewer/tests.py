from html.parser import HTMLParser
import json

from django.test import Client, TestCase
from django.utils import timezone
from mock.mock import MagicMock, patch

from geospaas.base_viewer.views import IndexView
from geospaas.catalog.models import Dataset


class BaseViewerHTMLParser(HTMLParser):
    """ A tiny parser for extraction and storage of data of specific tag(s)
    in html files. The specific tag(s) should be specificed
    in the handle_starttag method and the data is stored in
    the self.data.  In the case of inheritance, modify
    the 'handle_starttag method' based on your purpose of using this class."""

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
                    self.flag = True  # make the flag true to enable the storage action

    def handle_data(self, Data):
        if self.flag:  # just store the data of specified tags with the help of flag
            self.data.append(Data)
            # make it false AGAIN in order not to save the data from other tags of HTML
            self.flag = False


class IntegrationTestsForGUIWithNewBase(TestCase):
    '''Integration tests for GET and POST methods of GUI'''
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.client = Client()
        # this parser is configured to store the desired data of td tag into self.data
        self.parser = BaseViewerHTMLParser()

    def test_the_post_verb_of_GUI_with_proper_polygon(self):
        """shall return only the first dataset of fixtures
        in the specified placement of datasets inside the resulted HTML
        in the case of a POST request with a good choice of polygon"""
        res1 = self.client.post('/',
                                {'polygon':
                                 '{"type":"Polygon","coordinates":[[[0,0],[0,5],[5,5],[5,0],[0,0]]]}',
                                 'time_coverage_start': timezone.datetime(2000, 12, 29),
                                 'time_coverage_end': timezone.datetime(2020, 1, 1),
                                 'source': 1})
        self.assertEqual(res1.status_code, 200)
        self.parser.feed(str(res1.content))
        # the first dataset of fixtures must be in the html
        self.assertTrue(any([('file://localhost/some/test/file1.ext' in dat)
                             for dat in self.parser.data]))
        # the second dataset of fixturesshould not be in the html
        self.assertFalse(any([('file://localhost/some/test/file2.ext' in dat)
                              for dat in self.parser.data]))

    def test_the_post_verb_of_GUI_with_nonrelevant_polygon(self):
        """shall return 'No datasets are...' in the specified placement of datasets
        inside the resulted HTML in the case of a POST request with nonrelevant
        polygon apart from the polygon of databases datasets"""
        res2 = self.client.post('/',
                                {'polygon':
                                 '{"type":"Polygon","coordinates":[[[53.132629,-13.557892],[53.132629,4.346411],[73.721008,4.346411],[73.721008,-13.557892],[53.132629,-13.557892]]]}',
                                 'time_coverage_start': timezone.datetime(2000, 12, 29),
                                 'time_coverage_end': timezone.datetime(2020, 1, 1),
                                 'source': 1})
        self.assertEqual(res2.status_code, 200)
        self.parser.feed(str(res2.content))
        self.assertTrue(any([
            ('No datasets are available (or maybe no one is ingested)' in dat)
            for dat in self.parser.data]))

    def test_the_post_verb_of_GUI_without_polygon(self):
        """shall return the uri of fixtures' datasets in the specified placement
        of datasets inside the resulted HTML in the case of a POST request without
        any polygon from user """
        res3 = self.client.post('/', {
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'source': 1})
        self.assertEqual(res3.status_code, 200)
        self.parser.feed(str(res3.content))
        # both datasets must be in the html
        self.assertTrue(any([('file://localhost/some/test/file1.ext' in dat)
                             for dat in self.parser.data]))
        self.assertTrue(any([('file://localhost/some/test/file2.ext' in dat)
                             for dat in self.parser.data]))

    def test_the_post_verb_of_GUI_incorrect_dates_without_polygon(self):
        """shall return 'No datasets are...' in the specified placement of datasets
        inside the resulted HTML in the case of a POST request with incorrect dates
        from user and without any polygon from user"""
        res4 = self.client.post('/', {
            'time_coverage_start': timezone.datetime(2019, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'source': 1})
        self.assertEqual(res4.status_code, 200)
        self.parser.feed(str(res4.content))
        self.assertTrue(any([
            ('No datasets are available (or maybe no one is ingested)' in dat)
            for dat in self.parser.data]))

    def test_the_get_verb_of_GUI(self):
        """shall return ALL uri of fixtures' datasets in the specified placement
        of datasets inside the resulted HTML in the case of a GET request"""
        res5 = self.client.get('/')
        self.assertEqual(res5.status_code, 200)
        self.parser.feed(str(res5.content))
        # both datasets must be in the html
        self.assertTrue(any([('file://localhost/some/test/file1.ext' in dat)
                             for dat in self.parser.data]))
        self.assertTrue(any([('file://localhost/some/test/file2.ext' in dat)
                             for dat in self.parser.data]))


class IndexViewTests(TestCase):
    """ Unittesting for all functions inside the classed-based view of basic viewer """
    fixtures = ["vocabularies", "catalog"]
    @patch('geospaas.base_viewer.views.Dataset')
    def test_get_all_datasets(self, mock_dataset):
        """ Shall call CatalogDataset.objects.all() inside get_all_datasets """
        IndexView.get_all_datasets()
        mock_dataset.objects.all.assert_called_once()

    def test_get_filtered_datasets(self):
        """ Shall  call filter function from form class once """
        form = MagicMock()
        IndexView.get_filtered_datasets(form)
        form.filter.assert_called_once()

    def test_set_context(self):
        """ Shall  contain 'form' and 'datasets' in the context.
        Results should not be filtered by this function """
        form = MagicMock()
        ds = MagicMock()
        context = IndexView.set_context(form, ds)
        form.filter.assert_not_called()
        self.assertTrue('form' in context)
        self.assertTrue('datasets' in context)


class FilteringFunctionalityTests(TestCase):
    """ Unit tests for filter method which is placed inside the basic form"""
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.form = IndexView.form_class({'polygon': '',
                                          'time_coverage_start': timezone.datetime(2000, 12, 29),
                                          'time_coverage_end': timezone.datetime(2020, 1, 1),
                                          'source': 1})
        self.ds = Dataset.objects.all()
        self.form.is_valid()

    def tearDown(self):
        self.form = None
        self.ds = None

    def test_filtering_functionality_by_end_time(self):
        """Shall return (filter out) 'NERSC_test_dataset_titusen' dataset
        from fixtures based on their end date """
        # filtering by end time
        self.form.cleaned_data['time_coverage_start'] = timezone.datetime(
            2010, 1, 1, 0)
        self.form.cleaned_data['time_coverage_end'] = timezone.datetime(
            2010, 1, 1, 8)
        self.ds = self.form.filter(self.ds)
        self.assertEqual(self.ds.first().entry_id,
                         'NERSC_test_dataset_titusen')
        # only one of the fixture datasets should remain after filtering(titusen)
        self.assertEqual(len(self.ds), 1)

    def test_filtering_functionality_by_start_time(self):
        """Shall return (filter out) 'NERSC_test_dataset_tjuetusen' dataset
         from fixtures based on their start date """
        # filtering by start time
        self.form.cleaned_data['time_coverage_start'] = timezone.datetime(
            2010, 1, 2, 2)
        self.form.cleaned_data['time_coverage_end'] = timezone.datetime(
            2010, 1, 3, 4)
        self.ds = self.form.filter(self.ds)
        self.assertEqual(self.ds.first().entry_id,
                         'NERSC_test_dataset_tjuetusen')
        # only one of the fixture datasets should remain after filtering(tjuetusen)
        self.assertEqual(len(self.ds), 1)

    def test_filtering_functionality_by_source(self):
        """ shall return non of datasets because of filtering based on dummy source """

        self.form.cleaned_data['time_coverage_start'] = timezone.datetime(
            2010, 1, 2, 2)
        self.form.cleaned_data['time_coverage_end'] = timezone.datetime(
            2010, 1, 3, 4)
        self.form.cleaned_data['source'] = 9999 # dummy number for source id
        # filtering by source
        self.ds = self.form.filter(self.ds)
        # no dataset should remain as the result of filtering with dummy source
        self.assertEqual(len(self.ds), 0)

class GeometryGeojsonTests(TestCase):
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.client = Client()

    def test_get_valid_pk(self):
        """ shall return  valid GeoJSON with geometry """
        res = self.client.get('/geometry/1')
        self.assertEqual(res.status_code, 200)
        content = json.loads(res.content)
        self.assertEqual(content['type'], 'FeatureCollection')
        self.assertEqual(content['crs']['properties']['name'], 'EPSG:4326')
        self.assertEqual(content['features'][0]['geometry']['type'], 'Polygon')
        self.assertEqual(content['features'][0]['geometry']['coordinates'][0][0], [0,0])

    def test_get_invalid_pk(self):
        """ shall return  empty GeoJSON """
        res = self.client.get('/geometry/10')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b'{}')

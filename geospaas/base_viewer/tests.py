import json

from bs4 import BeautifulSoup
from django.test import Client, TestCase
from django.utils import timezone
from mock.mock import MagicMock, patch

from geospaas.base_viewer.forms import BaseSearchForm
from geospaas.base_viewer.views import IndexView
from geospaas.catalog.models import Dataset


class GUIIntegrationTests(TestCase):
    '''Integration tests for GET and POST methods of GUI'''
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.client = Client()

    @patch('django.conf.settings.SHOW_LOCAL_ADDRESS', return_value=True)
    def test_post_with_proper_polygon(self, mock_django_settings):
        """shall return only the first dataset of fixtures
        in the specified placement of datasets inside the resulted HTML
        in the case of a POST request with a good choice of polygon"""
        res = self.client.post('/tests/', {
            'polygon':
            '{"type":"Polygon","coordinates":[[[0,0],[0,5],[5,5],[5,0],[0,0]]]}',
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1)})
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("tr", class_="dataset_row")
        self.assertEqual(len(all_tds), 1)
        # the first dataset of fixtures must be in the html
        self.assertIn('file://localhost/some/test/file1.ext', all_tds[0].text)
        self.assertNotIn('file://localhost/some/test/file2.ext', all_tds[0].text)

    def test_post_with_proper_polygon_public_version(self):
        """shall not reveal any dataset of fixtures
        in the specified placement of datasets inside the resulted HTML
        in the case of a POST request with a good choice of polygon"""
        res = self.client.post('/tests/', {
            'polygon':
            '{"type":"Polygon","coordinates":[[[0,0],[0,5],[5,5],[5,0],[0,0]]]}',
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1)})
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("tr", class_="dataset_row")
        self.assertEqual(len(all_tds), 1)
        # the first dataset of fixtures must be in the html
        self.assertNotIn('file://localhost/some/test/file1.ext', all_tds[0].text)
        self.assertNotIn('file://localhost/some/test/file2.ext', all_tds[0].text)

    def test_post_with_irrelevant_polygon(self):
        """shall return 'No datasets are...' in the specified placement of datasets
        inside the resulted HTML in the case of a POST request with nonrelevant
        polygon apart from the polygon of databases datasets"""
        res = self.client.post('/tests/', {
            'polygon':
            ('{"type":"Polygon","coordinates":[[[53.132629,-13.557892],'
             '[53.132629,4.346411],[73.721008,4.346411],[73.721008,-13.'
             '557892],[53.132629,-13.557892]]]}'),
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1)})
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("td", class_="place_ds")
        self.assertEqual(all_tds[0].text,
                        'No datasets found')

    @patch('django.conf.settings.SHOW_LOCAL_ADDRESS', return_value=True)
    def test_post_without_polygon(self, mock_django_settings):
        """shall return the uri of fixtures' datasets in the specified placement
        of datasets inside the resulted HTML in the case of a POST request without
        any polygon from user """
        res = self.client.post('/tests/', {
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'source': 1})
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("tr", class_="dataset_row")
        self.assertEqual(len(all_tds), 2)
        self.assertIn('file://localhost/some/test/file1.ext', all_tds[0].text)
        self.assertIn('file://localhost/some/test/file2.ext', all_tds[1].text)

    def test_post_without_polygon_public_version(self):
        """shall not reveal the uri of fixtures' datasets (presumably confidential) in the specified
         placement of datasets inside the resulted HTML in the case of a POST request without
        any polygon from user """
        res = self.client.post('/tests/', {
            'time_coverage_start': timezone.datetime(2000, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'source': 1})
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("tr", class_="dataset_row")
        self.assertEqual(len(all_tds), 2)
        self.assertNotIn('file://localhost/some/test/file1.ext', all_tds[0].text)
        self.assertNotIn('file://localhost/some/test/file2.ext', all_tds[1].text)

    def test_post_with_incorrect_dates_without_polygon(self):
        """shall return 'No datasets are...' in the specified placement of datasets
        inside the resulted HTML in the case of a POST request with incorrect dates
        from user and without any polygon from user"""
        res = self.client.post('/tests/', {
            'time_coverage_start': timezone.datetime(2019, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1)})
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("td", class_="place_ds")
        self.assertEqual(all_tds[0].text,
                        'No datasets found')

    @patch('geospaas.base_viewer.views.Paginator')
    def test_post_with_correct_dates_with_page(self, mock_paginator):
        """ post with page=100 shall call Paginator.get_page with 100 """
        res = self.client.post('/tests/', {
            'time_coverage_start': timezone.datetime(2019, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1),
            'page': 100})
        mock_paginator.return_value.get_page.assert_called_with('100')

    @patch('geospaas.base_viewer.views.Paginator')
    def test_post_or_get_without_page(self, mock_paginator):
        """ post without page shall call Paginator.get_page with 1 """
        res = self.client.post('/tests/', {
            'time_coverage_start': timezone.datetime(2019, 12, 29),
            'time_coverage_end': timezone.datetime(2020, 1, 1)})
        mock_paginator.return_value.get_page.assert_called_with(1)
        res = self.client.get('/tests/')
        mock_paginator.return_value.get_page.assert_called_with(1)

    @patch('django.conf.settings.SHOW_LOCAL_ADDRESS', return_value=True)
    def test_get(self, mock_django_settings):
        """shall return ALL uri of fixtures' datasets in the specified placement
        of datasets inside the resulted HTML in the case of a GET request"""
        res = self.client.get('/tests/')
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("tr", class_="dataset_row")
        self.assertEqual(len(all_tds), 2)
        self.assertIn('file://localhost/some/test/file1.ext', all_tds[0].text)
        self.assertIn('file://localhost/some/test/file2.ext', all_tds[1].text)
        grefs=soup.find_all("tr", class_="dataset_row")
        self.assertEqual(grefs[0].attrs['ajax_url'], '/tests/geometry/1')

    def test_get_public_version(self):
        """shall not reveals uri of fixtures' datasets (presumably confidential) in the specified
         placement of datasets inside the resulted HTML in the case of a GET request"""
        res = self.client.get('/tests/')
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(str(res.content), features="lxml")
        all_tds = soup.find_all("tr", class_="dataset_row")
        self.assertEqual(len(all_tds), 2)
        self.assertNotIn('file://localhost/some/test/file1.ext', all_tds[0].text)
        self.assertNotIn('file://localhost/some/test/file2.ext', all_tds[1].text)
        grefs=soup.find_all("tr", class_="dataset_row")
        self.assertEqual(grefs[0].attrs['ajax_url'], '/tests/geometry/1')


class IndexViewTests(TestCase):
    """ Unittesting for all functions inside the classed-based view of basic viewer """
    fixtures = ["vocabularies", "catalog"]

    @patch('geospaas.base_viewer.views.Dataset')
    def test_get_all_datasets(self, mock_dataset):
        """ Shall call Dataset.objects.order_by() inside get_all_datasets """
        IndexView.get_all_datasets()
        mock_dataset.objects.order_by.assert_called_once()

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
        self.assertTrue('page_obj' in context)

    def test_paginate(self):
        """
        Shall return paginator with 2 pages and only one dataset
        when paginate_by set to 1
        """
        IndexView.paginate_by = 1
        ds = Dataset.objects.order_by('time_coverage_start')
        request = MagicMock()
        request.POST = dict(page=1)
        page_obj = IndexView.paginate(ds, request)
        self.assertEqual(page_obj.number, 1)
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())
        self.assertEqual(page_obj.object_list.count(), 1)


class BaseSearchFormTests(TestCase):
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.ds = Dataset.objects.all()

    def test_filter_by_end_time(self):
        """Shall return (filter out) 'NERSC_test_dataset_titusen' dataset
        from fixtures based on their end date """
        # filtering by end time
        form = BaseSearchForm({
            'time_coverage_start': timezone.datetime(2010, 1, 1, 0, tzinfo=timezone.utc),
            'time_coverage_end': timezone.datetime(2010, 1, 1, 8, tzinfo=timezone.utc),
        })
        form.is_valid()
        ds = form.filter(self.ds)
        self.assertEqual(ds.first().entry_id,
                         'NERSC_test_dataset_titusen')
        # only one of the fixture datasets should remain after filtering(titusen)
        self.assertEqual(len(ds), 1)

    def test_filter_by_start_time(self):
        """Shall return (filter out) 'NERSC_test_dataset_tjuetusen' dataset
         from fixtures based on their start date """
        # filtering by start time
        form = BaseSearchForm({
            'time_coverage_start': timezone.datetime(2010, 1, 2, 2, tzinfo=timezone.utc),
            'time_coverage_end': timezone.datetime(2010, 1, 3, 4, tzinfo=timezone.utc),
        })
        form.is_valid()

        ds = form.filter(self.ds)
        self.assertEqual(ds.first().entry_id,
                         'NERSC_test_dataset_tjuetusen')
        # only one of the fixture datasets should remain after filtering(tjuetusen)
        self.assertEqual(len(ds), 1)

    def test_filter_by_valid_source(self):
        """ shall return both datasets """
        form = BaseSearchForm({
            'time_coverage_start': timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            'time_coverage_end': timezone.datetime(2020, 1, 1, 1, tzinfo=timezone.utc),
            'source': [1],
        })
        form.is_valid()
        self.assertIn('source', form.cleaned_data)
        # filtering by source
        ds = form.filter(self.ds)
        # no dataset should remain as the result of filtering with dummy source
        self.assertEqual(len(ds), 2)

    def test_filter_by_invalid_source(self):
        """ shall return both datasets """
        form = BaseSearchForm({
            'time_coverage_start': timezone.datetime(2000, 1, 1, tzinfo=timezone.utc),
            'time_coverage_end': timezone.datetime(2020, 1, 1, 1, tzinfo=timezone.utc),
            'source': [10],
        })
        form.is_valid()
        self.assertNotIn('source', form.cleaned_data)
        # filtering by source
        ds = form.filter(self.ds)
        # no dataset should remain as the result of filtering with dummy source
        self.assertEqual(len(ds), 2)

class GeometryGeojsonTests(TestCase):
    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.client = Client()

    def test_get_valid_pk(self):
        """ shall return  valid GeoJSON with geometry """
        res = self.client.get('/tests/geometry/1')
        self.assertEqual(res.status_code, 200)
        content = json.loads(res.content)
        self.assertEqual(content['type'], 'FeatureCollection')
        self.assertEqual(content['crs']['properties']['name'], 'EPSG:4326')
        self.assertEqual(content['features'][0]['geometry']['type'], 'Polygon')
        self.assertEqual(content['features'][0]['geometry']['coordinates'][0][0], [0,0])

    def test_get_invalid_pk(self):
        """ shall return  empty GeoJSON """
        res = self.client.get('/tests/geometry/10')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b'{}')

import os
import json
from mock import patch, PropertyMock, Mock, MagicMock, DEFAULT

import django.db.utils
from django.test import TestCase
from django.utils import timezone
from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos import WKTReader
from django.core.management import call_command
from django.core.exceptions import ValidationError
from io import StringIO
from django.conf import settings
from django.core.management.base import CommandError

from geospaas.vocabularies.models import Parameter
from geospaas.catalog.models import *


class TagTests(TestCase):
    """Tests for the Tag model"""

    def test_validate_tag(self):
        """Test the validation function for the tag value argument"""
        self.assertIsNone(validate_tag({'foo': 'bar'}))
        with self.assertRaises(ValidationError):
            validate_tag('foo')

    def test_str(self):
        """"""
        self.assertEqual(
            str(Tag(name='foo', value='bar')),
            '(foo: bar)'
        )


class DatasetTests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    @patch('os.path.isfile')
    def test_dataset(self, mock_isfile):
        mock_isfile.return_value = True
        ''' Shall create Dataset instance '''
        et = 'Test dataset'
        id = 'NERSC_test_dataset_1'
        ds = Dataset(
                entry_id = id,
                entry_title=et,
                summary = 'This is a quite short summary about the test' \
                            ' dataset.',
                time_coverage_start=timezone.datetime(2010,1,1,
                    tzinfo=timezone.utc),
                time_coverage_end=timezone.datetime(2010,1,2,
                    tzinfo=timezone.utc),
                location='SRID=4326;POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))')
        ds.save()
        self.assertEqual(ds.entry_id, id)
        self.assertEqual(ds.entry_title, et)

        # Shall create new DatasetURI
        ds_uri1, cr1 = DatasetURI.objects.get_or_create(uri='file://localhost/test_name1.nc',
                                                      dataset=ds)
        self.assertIsInstance(ds_uri1, DatasetURI)
        self.assertEqual(cr1, True)

        # Shall NOT create new DatasetURI
        ds_uri2, cr2 = DatasetURI.objects.get_or_create(uri='file://localhost/test_name1.nc',
                                                      dataset=ds)
        self.assertEqual(ds_uri1, ds_uri2)
        self.assertEqual(cr2, False)

        # Shall create new DatasetURI
        ds_uri3, cr3 = DatasetURI.objects.get_or_create(uri='file://localhost/test_name2.nc',
                                                      dataset=ds)
        self.assertIsInstance(ds_uri3, DatasetURI)
        self.assertEqual(cr3, True)

    def test_entry_id_is_wrong(self):
        et = 'Test dataset'
        id = 'NERSC/test/dataset/1'
        ds = Dataset(
                entry_id = id,
                entry_title=et,
                summary = 'This is a quite short summary about the test' \
                            ' dataset.',
                time_coverage_start=timezone.datetime(2010,1,1,
                    tzinfo=timezone.utc),
                time_coverage_end=timezone.datetime(2010,1,2,
                    tzinfo=timezone.utc),
                location='SRID=4326;POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))')
        with self.assertRaises(ValidationError):
            ds.full_clean()

    def test_entry_id_is_correct(self):
        et = 'Test dataset'
        id = 'NERSC_test_dataset_1.2'
        ds = Dataset(
                entry_id = id,
                entry_title=et,
                summary = 'This is a quite short summary about the test' \
                            ' dataset.',
                time_coverage_start=timezone.datetime(2010,1,1,
                    tzinfo=timezone.utc),
                time_coverage_end=timezone.datetime(2010,1,2,
                    tzinfo=timezone.utc),
                location='SRID=4326;POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))')
        ds.full_clean()
        self.assertEqual(ds.entry_id, id)

    def test_str(self):
        """Test the string representation of Dataset"""
        self.assertEqual(
            str(Dataset(entry_id='foo')),
            'foo')


class DatasetURITests(TestCase):

    fixtures = ["vocabularies", "catalog"]

    def setUp(self):
        self.dataset = Dataset.objects.get(pk=1)

    @patch('os.path.isfile')
    def test_DatasetURI_created(self, mock_isfile):
        mock_isfile.return_value = True
        uri = 'file://localhost/this/is/some/file'
        dsuri = DatasetURI(uri=uri, dataset=self.dataset)
        dsuri.save()
        self.assertEqual(dsuri.uri, uri)

    def test_str(self):
        """Test the string representation of DatasetURI"""
        self.assertEqual(
            str(DatasetURI(uri='https://bar/foo', dataset=Dataset(entry_id='foo'))),
            'https://bar/foo')

    def test_protocol(self):
        """Test getting the protocol of the URL"""
        self.assertEqual(
            DatasetURI(uri='https://bar/foo', dataset=Dataset(entry_id='foo')).protocol(),
            'https')


class PersonnelTests(TestCase):
    ''' We should add user admin with, e.g., with the Personnel model. Skip
    testing before that is in place
    '''
    pass


class RoleTests(TestCase):
    pass


class TestCountCommand(TestCase):
    fixtures = ['vocabularies', 'catalog']
    def test_count_command(self):
        out = StringIO()
        call_command('count', stdout=out)
        self.assertEqual('Found 2 matching datasets\n', out.getvalue())

        out = StringIO()
        call_command('count', start='2010-01-02', stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

        out = StringIO()
        call_command('count', extent=[0, 10, 0, 10], stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

        out = StringIO()
        with self.assertRaises(CommandError) as ce:
            call_command('count', geojson='fake_filename', stdout=out)
        self.assertIn('GeoJSON file', ce.exception.args[0])

    def test_count_command_bad_start(self):
        out = StringIO()
        with self.assertRaises(CommandError) as ce:
            call_command('count', start='abrakadabra', stdout=out)
        self.assertIn('Not a valid date', ce.exception.args[0])

    @patch('geospaas.utils.processing_base_command.open')
    def test_count_command_good_geojson_polygon(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = '{ "type": "Polygon", "coordinates": [ [ [ -1, -1 ], [ -1, 11 ], [ 11, 11 ], [ 11, -1 ], [ -1, -1 ] ] ] }'
        out = StringIO()
        call_command('count', geojson=os.path.realpath(__file__), stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

    @patch('geospaas.utils.processing_base_command.open')
    def test_count_command_good_geojson_point(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = '{ "type": "Point", "coordinates": [ 1, 1 ] }'
        out = StringIO()
        call_command('count', geojson=os.path.realpath(__file__), stdout=out)
        self.assertEqual('Found 1 matching datasets\n', out.getvalue())

    @patch('geospaas.utils.processing_base_command.open')
    def test_count_command_wrong_geojson_content(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = 'wrong json'
        out = StringIO()
        with self.assertRaises(CommandError) as ce:
            call_command('count', geojson=os.path.realpath(__file__), stdout=out)
        self.assertIn('Failed to read valid GeoJSON from', ce.exception.args[0])

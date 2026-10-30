"""Test suite for ingesters"""

import logging
import unittest.mock as mock
import uuid
from datetime import datetime, timezone

import django.test
import yaml
from geospaas.catalog.models import Dataset, DatasetURI, Tag
from geospaas.vocabularies.models import Keyword, Parameter

import geospaas.harvesting.ingesters as ingesters
from . import TEST_FILES_PATH


class IngesterTestCase(django.test.TransactionTestCase):
    """Test the base ingester class"""

    def setUp(self):
        self.patcher_param_count = mock.patch.object(Parameter.objects, 'count')
        self.mock_param_count = self.patcher_param_count.start()
        self.mock_param_count.return_value = 2
        self.ingester = ingesters.Ingester()
        with open(TEST_FILES_PATH / 'dataset_metadata.yml', encoding='utf-8') as f_h:
            self.dataset_metadata = yaml.safe_load(f_h)
        self.dataset_metadata['time_coverage_start'] = datetime.strptime(
            self.dataset_metadata['time_coverage_start'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        self.dataset_metadata['time_coverage_end'] = datetime.strptime(
            self.dataset_metadata['time_coverage_end'], '%Y-%m-%d').replace(tzinfo=timezone.utc)

    def tearDown(self):
        self.patcher_param_count.stop()

    def test_max_db_threads_type_error(self):
        """An exception should be raised if the max_db_threads argument
        to the constructor is not an integer
        """
        with self.assertRaises(TypeError):
            ingesters.Ingester(max_db_threads='2')

    def _create_dummy_dataset(self, entry_id):
        """Create dummy dataset for testing purposes"""
        dataset = Dataset(entry_id=entry_id)
        dataset.save()
        return (dataset, True)

    def _create_dummy_dataset_uri(self, uri, dataset):
        """Create dummy dataset URI for testing purposes"""
        dataset_uri = DatasetURI(uri=uri, dataset=dataset)
        dataset_uri.save()
        return (dataset_uri, True)

    def _prepare_dataset_attributes(self):
        """Test preparing the attributes needed to create a Dataset"""
        self.maxDiff = None
        normalized_attributes = self.dataset_metadata.copy()
        dataset_attributes, dataset_parameters_list = (
            ingesters.Ingester._prepare_dataset_attributes(normalized_attributes))
        self.assertDictEqual(
            dataset_attributes,
            {
                'entry_title': 'title',
                'entry_id': 'id',
                'summary': 'sum-up',
                'time_coverage_start': datetime(2022, 1, 1, tzinfo=timezone.utc),
                'time_coverage_end': datetime(2022, 1, 2, tzinfo=timezone.utc),
                'location': 'POINT(10 11)',
            })
        self.assertListEqual(
            dataset_parameters_list,
            [
                Parameter.get(standard_name='parameter', short_name='param', units='bananas'),
                Parameter.get(standard_name='latitude', short_name='lat', units='degrees_north')
            ])

    def test_ingest_dataset(self):
        """Test ingesting a dataset from a DatasetInfo object"""
        parameters = [
            Parameter(data={
                'standard_name': 'parameter',
                'short_name': 'param',
                'units': 'bananas'}),
            Parameter(data={
                'standard_name': 'latitude',
                'short_name': 'lat',
                'units': 'degrees_north'})
        ]
        keywords = [
            Keyword(kind='gcmd_platform', data={
                'Basis': 'Space-based Platforms',
                'Category': '',
                'Long_Name': '',
                'Short_Name': '',
                'Sub_Category': ''})
        ]
        tags_kwargs = [{'name': 'custom_tag', 'value': 'something'}]
        for i in [*parameters, *keywords]:
            i.save()

        self.ingester._ingest_dataset(( # pylint: disable=protected-access
            {'entry_id': 'foo'},
            'https://bar/foo.nc',
            keywords, parameters, tags_kwargs),)

        dataset = Dataset.objects.last()
        self.assertEqual(dataset.entry_id, 'foo')
        self.assertListEqual(list(dataset.parameters.all()), parameters)
        self.assertListEqual(list(dataset.keywords.all()), keywords)
        self.assertListEqual(
            list(dataset.tags.all()), [Tag.objects.get(**tkw) for tkw in tags_kwargs])

    def test_ingest_same_uri_twice(self):
        """Ingestion of the same URI must not create duplicates"""
        uri = 'https://bar/foo.nc'
        to_ingest = ({'entry_id': 'foo'}, [uri], [], [], [])
        self.ingester._ingest_dataset(to_ingest)
        created_uris, existing_uris, _, dataset_status = self.ingester._ingest_dataset(to_ingest)

        self.assertEqual(dataset_status, ingesters.OperationStatus.NOOP)
        self.assertListEqual(created_uris, [])
        self.assertListEqual(existing_uris, [DatasetURI.objects.get(uri=uri)])
        self.assertEqual(Dataset.objects.count(), 1)

    def test_ingest_same_dataset_different_uri(self):
        """Ingestion of the same URI must not happen twice and the attempt must be logged"""
        uris = ['http://test.uri1/dataset',
                'http://test.uri2/dataset']

        for uri in uris:
            self.ingester._ingest_dataset(({'entry_id': 'foo'}, [uri], [], [], []))

        self.assertEqual(Dataset.objects.count(), 1)
        self.assertEqual(DatasetURI.objects.count(), 2)
        # check that both URIs have the same dataset
        self.assertEqual(*[
            DatasetURI.objects.get(uri=uri).dataset.entry_id
            for uri in uris])

    def test_ingest_update(self):
        """Test updating a dataset while ingesting"""
        uri = 'http://test.uri/dataset'
        entry_id = 'foo'
        tag_kwargs = {'name': 'custom_tag', 'value': 'hello'}
        to_ingest = ({'entry_id': entry_id}, [uri], [], [], [])
        to_ingest_update = (
            {'entry_id': entry_id, 'entry_title': 'bar'}, [uri], [], [], [tag_kwargs])

        ingester = ingesters.Ingester(update=True)
        ingester._ingest_dataset(to_ingest)
        created_uris, existing_uris, _, dataset_status = ingester._ingest_dataset(to_ingest_update)

        self.assertEqual(dataset_status, ingesters.OperationStatus.UPDATED)
        self.assertListEqual(created_uris, [])
        self.assertListEqual(existing_uris, [DatasetURI.objects.get(uri=uri)])
        self.assertEqual(Dataset.objects.count(), 1)
        dataset = Dataset.objects.get(entry_id=entry_id)
        self.assertEqual(dataset.entry_id, 'foo')
        self.assertEqual(dataset.entry_title, 'bar')
        self.assertListEqual(list(dataset.tags.all()), [Tag.objects.get(**tag_kwargs)])

    def test_ingest_no_entry_id(self):
        """Test ingesting a dataset when no entry_id is provided"""
        uri = 'https://bar/foo.nc'
        created_uris, existing_uris, dataset_entry_id, dataset_status = (
            self.ingester._ingest_dataset(( # pylint: disable=protected-access
                {'entry_title': 'qux'}, [uri], [], [], [])))
        self.assertListEqual(created_uris, [DatasetURI.objects.get(uri=uri)])
        self.assertListEqual(existing_uris, [])
        self.assertIsInstance(dataset_entry_id, uuid.UUID)
        self.assertEqual(dataset_status, ingesters.OperationStatus.CREATED)

    def test_log_on_ingestion_error(self):
        """The cause of the error must be logged if an exception is raised while ingesting"""
        with mock.patch.object(ingesters.Ingester, '_ingest_dataset') as mock_ingest_dataset:
            mock_ingest_dataset.side_effect = TypeError('error message')
            with self.assertLogs(self.ingester.logger, level=logging.ERROR) as logger_cm:
                self.ingester.ingest([({'entry_id': 'foo'}, ['uri'], [], [], [])])
            self.assertEqual(logger_cm.records[0].message,
                             "Error during ingestion: error message")
            self.assertIs(logger_cm.records[0].exc_info[0], TypeError)

    def test_log_on_ingestion_success(self):
        """All ingestion successes must be logged"""
        with mock.patch.object(ingesters.Ingester, '_ingest_dataset') as mock_ingest_dataset:
            mock_ingest_dataset.return_value = (
                [mock.Mock(uri='uri')],
                [],
                'foo',
                ingesters.OperationStatus.CREATED,
            )
            with self.assertLogs(self.ingester.logger, level=logging.INFO) as logger_cm:
                self.ingester.ingest([({'entry_id': 'foo'}, ['uri'], [], [], [])])
                self.assertEqual(logger_cm.records[0].message,
                                 "Successfully created dataset 'foo'. Created URIs: ['uri']")

    def test_log_on_update(self):
        """Test logging a successful update"""
        with mock.patch.object(ingesters.Ingester, '_ingest_dataset') as mock_ingest_dataset:
            mock_ingest_dataset.return_value = (
                [],
                [mock.Mock(uri='uri')],
                'foo',
                ingesters.OperationStatus.UPDATED,
            )
            with self.assertLogs(self.ingester.logger, level=logging.INFO) as logger_cm:
                self.ingester.ingest([({'entry_id': 'foo'}, ['uri'], [], [], [])])
                self.assertEqual(logger_cm.records[0].message,
                                 "Successfully updated dataset 'foo'. URIs already exist: ['uri']")

    def test_log_existing_dataset(self):
        """Test logging a successful update"""
        with mock.patch.object(ingesters.Ingester, '_ingest_dataset') as mock_ingest_dataset:
            mock_ingest_dataset.return_value = (
                [],
                [mock.Mock(uri='uri')],
                'foo',
                ingesters.OperationStatus.NOOP,
            )
            with self.assertLogs(self.ingester.logger, level=logging.INFO) as logger_cm:
                self.ingester.ingest([({'entry_id': 'foo'}, ['uri'], [], [], [])])
                self.assertEqual(logger_cm.records[0].message,
                                 "Dataset already exists: 'foo'. URIs already exist: ['uri']")

    def test_log_on_ingestion_same_dataset_different_uri(self):
        """A message must be logged when a URI is added to an existing
        dataset
        """
        with mock.patch.object(ingesters.Ingester, '_ingest_dataset') as mock_ingest_dataset:
            mock_ingest_dataset.return_value = (
                [mock.Mock(uri='uri')],
                [],
                'foo',
                ingesters.OperationStatus.NOOP,
            )
            with self.assertLogs(self.ingester.logger, level=logging.INFO) as logger_cm:
                self.ingester.ingest([({'entry_id': 'foo'}, ['uri'], [], [], [])])
                self.assertEqual(logger_cm.records[0].message,
                                 "Dataset already exists: 'foo'. Created URIs: ['uri']")

    def test_keyboard_interruption(self):
        """Test that keyboard interrupts are managed properly"""
        mock_futures = (mock.Mock(), KeyboardInterrupt)
        with mock.patch('concurrent.futures.ThreadPoolExecutor.submit',
                        side_effect=mock_futures) as mock_submit, \
                mock.patch('concurrent.futures.as_completed') as mock_as_completed:
            with self.assertRaises(KeyboardInterrupt), \
                 self.assertLogs(self.ingester.logger, level=logging.DEBUG):
                self.ingester.ingest([mock.Mock(), mock.Mock()])
            mock_futures[0].cancel.assert_called()

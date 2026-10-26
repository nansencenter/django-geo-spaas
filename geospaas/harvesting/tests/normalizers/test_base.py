"""Tests for the base GeoSPaaS normalizer"""
import logging
import pickle
import shutil
import tempfile
import threading
import unittest
import unittest.mock as mock
from pathlib import Path

import geospaas.harvesting.crawlers.base as crawlers_base
import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo


class MetadataNormalizerTestCase(unittest.TestCase):
    """Tests for MetadataNormalizer"""

    def setUp(self):
        self.normalizer = normalizers.base.MetadataNormalizer()

    def test_str(self):
        """Test __str__"""
        class TestNormalizer(normalizers.base.MetadataNormalizer):
            name = 'test'
        self.assertEqual(str(TestNormalizer()), 'test')

    def test_get_entry_title(self):
        """get_entry_title() should return an empty string"""
        self.assertEqual(self.normalizer.get_entry_title(DatasetInfo('')), '')

    def test_get_entry_id(self):
        """get_entry_id() should be raise a NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.normalizer.get_entry_id(DatasetInfo(''))

    def test_summary(self):
        """get_summary() should return an empty string
        """
        self.assertEqual(self.normalizer.get_summary(DatasetInfo('')), '')

    def test_get_time_coverage_start(self):
        """get_time_coverage_start() should be raise a
        NotImplementedError
        """
        with self.assertRaises(NotImplementedError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))

    def test_get_time_coverage_end(self):
        """get_time_coverage_end() should be raise a
        NotImplementedError
        """
        with self.assertRaises(NotImplementedError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))

    def test_get_location_geometry(self):
        """get_location_geometry() should be raise a
        NotImplementedError
        """
        with self.assertRaises(NotImplementedError):
            self.normalizer.get_location_geometry(DatasetInfo(''))

    def test_get_keywords(self):
        """get_keywords() should be return and empty list"""
        self.assertListEqual(self.normalizer.get_keywords(DatasetInfo('')), [])

    def test_get_tags(self):
        """Should return en empty list"""
        self.assertListEqual(self.normalizer.get_tags(DatasetInfo('')), [])

    def test_get_dataset_parameters(self):
        """Test getting parameters from the 'raw_dataset_parameters'
        attribute
        """
        with mock.patch('geospaas.harvesting.normalizers.utils.create_parameter_list'
                        ) as mock_create_parameter_list:
            mock_create_parameter_list.return_value = ['foo', 'bar']
            self.assertCountEqual(
                self.normalizer.get_dataset_parameters(
                    DatasetInfo('', {'raw_dataset_parameters': ['baz', 'qux']})),
                ['foo', 'bar'])

    def test_get_dataset_parameters_no_raw_parameters(self):
        """get_dataset_parameters() should return an empty string when
        'raw_dataset_parameters' is not present in the raw metadata
        """
        self.assertListEqual(self.normalizer.get_dataset_parameters(DatasetInfo('')), [])

    def test_get_extra_urls(self):
        """Should return an empty list by default"""
        self.assertListEqual(self.normalizer.get_extra_urls(DatasetInfo('')), [])

    def test_normalize(self):
        """Test that the normalize method returns the right attributes
        """

        class TestNormalizer(normalizers.base.MetadataNormalizer):
            """Normalizer class inheriting from
            GeoSPaaSMetadataNormalizer for testing purposes
            """

            def get_entry_title(self, raw_metadata):
                """Get the entry title from the raw metadata"""
                return 'entry_title'

            def get_entry_id(self, raw_metadata):
                """Get the entry ID from the raw metadata"""
                return 'entry_id'

            def get_summary(self, raw_metadata):
                """Get the summary from the raw metadata"""
                return 'summary'

            def get_time_coverage_start(self, raw_metadata):
                """Get the start of the time coverage from the raw metadata"""
                return 'time_coverage_start'

            def get_time_coverage_end(self, raw_metadata):
                """Get the end of the time coverage from the raw metadata"""
                return 'time_coverage_end'

            def get_keywords(self, dataset_info):
                return [{'kind': 'gcmd_instrument', 'data': {'Short_Name': 'instrument'}}]

            def get_location_geometry(self, raw_metadata):
                """Get the location geometry (in WKT or GeoJSON) from the raw
                metadata
                """
                return 'location_geometry'

            def get_dataset_parameters(self, raw_metadata):
                """Get the dataset parameters, if any, from the raw metadata"""
                return ['dataset_parameters']

            def get_tags(self, dataset_info):
                return [{'name': 'collection', 'value': 'test'}]

            def get_extra_urls(self, dataset_info):
                return ['https://dl.foo']

        self.assertTupleEqual(
            TestNormalizer().normalize(DatasetInfo('https://foo')),
            (
                {
                    'entry_title': 'entry_title',
                    'entry_id': 'entry_id',
                    'summary': 'summary',
                    'location': 'location_geometry',
                    'time_coverage_start': 'time_coverage_start',
                    'time_coverage_end': 'time_coverage_end',
                },
                ['https://foo', 'https://dl.foo'],
                [{'kind': 'gcmd_instrument', 'data': {'Short_Name': 'instrument'}}],
                ['dataset_parameters'],
                [{'name': 'collection', 'value': 'test'}],
            )
        )

        self.assertTupleEqual(
            TestNormalizer(
                location='force_location',
                time_coverage_start='force_time_coverage_start',
                time_coverage_end='force_time_coverage_end'
            ).normalize(DatasetInfo('https://foo')),
            (
                {
                    'entry_title': 'entry_title',
                    'entry_id': 'entry_id',
                    'summary': 'summary',
                    'location': 'force_location',
                    'time_coverage_start': 'force_time_coverage_start',
                    'time_coverage_end': 'force_time_coverage_end',
                },
                ['https://foo', 'https://dl.foo'],
                [{'kind': 'gcmd_instrument', 'data': {'Short_Name': 'instrument'}}],
                ['dataset_parameters'],
                [{'name': 'collection', 'value': 'test'}],
            )
        )


class StreamMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for StreamMetadataNormalizer
    """

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.old_ingestion_path = normalizers.base.StreamMetadataNormalizer.FAILED_INGESTIONS_PATH
        self.old_max_failed = normalizers.base.StreamMetadataNormalizer.MAX_FAILED
        normalizers.base.StreamMetadataNormalizer.FAILED_INGESTIONS_PATH = self.tmp_dir
        normalizers.base.StreamMetadataNormalizer.MAX_FAILED = 2

    def tearDown(self):
        normalizers.base.StreamMetadataNormalizer.FAILED_INGESTIONS_PATH = self.old_ingestion_path
        normalizers.base.StreamMetadataNormalizer.MAX_FAILED = self.old_max_failed
        shutil.rmtree(self.tmp_dir)

    class TestCrawler(crawlers_base.Crawler):
        """Crawler used for testing the CrawlerIterator"""

        def crawl(self):
            for url in ['https://foo', 'https://bar', 'https://baz']:
                yield crawlers_base.DatasetInfo(url)

    class TestNormalizer(normalizers.base.MetadataNormalizer):
        """Normalizer used for testing"""

        def normalize(self, dataset_info):
            #used for testing error management
            if dataset_info.url == 'https://bar':
                raise RuntimeError()
            elif dataset_info.url == 'https://baz':
                # bypass the broad exception catch in
                # _thread_normalize() to check handling
                # of exceptions happening in that method
                raise BaseException() # pylint: disable=broad-exception-raised

            return ({'entry_id': 'foo'}, dataset_info.url, [], [], [])

    def test_iterating(self):
        """Test iterating over normalization results"""
        crawler = self.TestCrawler.from_kwargs()
        stream_normalizer = self.TestNormalizer().normalize_stream(crawler.crawl())
        with self.assertLogs(normalizers.base.StreamMetadataNormalizer.logger,
                             level=logging.ERROR) as scm:
            iterator = iter(stream_normalizer)
            iterator.manager_thread.join()

        self.assertIs(scm.records[0].exc_info[0], RuntimeError)
        self.assertIs(scm.records[1].exc_info[0], BaseException)

        results = list(iterator)

        self.assertListEqual(results, [({'entry_id': 'foo'}, 'https://foo', [], [], [])])

        failed_ingestion_files = list(self.tmp_dir.iterdir())
        self.assertEqual(len(failed_ingestion_files), 1)
        self.assertTrue(str(failed_ingestion_files[0]).endswith(stream_normalizer.RECOVERY_SUFFIX))

    def test_pickle_list_elements(self):
        """Test pickling a list of objects"""
        # create a crawler iterator without starting the processing threads
        crawler = self.TestCrawler.from_kwargs()
        with mock.patch('threading.Thread'):
            stream_normalizer = self.TestNormalizer().normalize_stream(crawler.crawl())
        objects_to_pickle = [1, 'one', 2.2]
        reference = list(objects_to_pickle)  # needed because the list will be cleared
        with tempfile.TemporaryDirectory() as tmp_dir, self.assertLogs(stream_normalizer.logger):
            file_path = Path(tmp_dir, 'random_objects.pickle')
            # pickle various objects to a temporary file
            stream_normalizer._pickle_list_elements(objects_to_pickle, file_path)

            # retrieve the pickled objects and check they are the same
            # as the ones which were pickled
            unpickled_objects = []
            with open(file_path, 'rb') as pickle_file:
                while True:
                    try:
                        unpickled_objects.append(pickle.load(pickle_file))
                    except EOFError:
                        break

            self.assertListEqual(unpickled_objects, reference)
            self.assertFalse(objects_to_pickle)  # check that the list has been cleared

    def test_thread_manage_failed_ingestions(self):
        """Test the processing of failed ingestions"""
        # create a crawler iterator without starting the processing threads
        stream_normalizer = self.TestNormalizer().normalize_stream([])
        with mock.patch('threading.Thread'):
            iter(stream_normalizer)

        # start the thread
        thread = threading.Thread(target=stream_normalizer._thread_manage_failed_normalizing)
        with self.assertLogs(stream_normalizer.logger, level=logging.INFO) as log_manager:
            thread.start()
            # put two items in the failed queue (one more than the
            # max number of items per file)
            items_to_pickle = [
                (crawlers_base.DatasetInfo('foo', {}), RuntimeError()),
                (crawlers_base.DatasetInfo('baz', {}), ValueError()),
                (crawlers_base.DatasetInfo('quux', {}), KeyError())
            ]
            for item in items_to_pickle:
                stream_normalizer._failed.put(item)
            # stop the thread
            stream_normalizer._failed.put(normalizers.base.Stop)
            # wait for the thread to stop
            thread.join()

        # check that one file is created
        failed_dir_contents = list(self.tmp_dir.iterdir())
        self.assertEqual(len(failed_dir_contents), 1)

        with open(Path(self.tmp_dir, failed_dir_contents[0]), 'rb') as pickle_file:
            pickled_objects = [
                pickle.load(pickle_file) for _ in range(len(items_to_pickle))
            ]

            with self.assertRaises(EOFError):
                pickle.load(pickle_file)

        # check the contents of the file
        self.assertTrue(all(
            (to_pickle[0] == result[0],
             type(to_pickle[1]) == type(result[1]) and to_pickle[1].args == result[1].args)
            for to_pickle, result in zip(items_to_pickle, pickled_objects)
        ))

        # check that the dump method has been called twice
        # (because the number of items exceeds the max number
        # of items per file)
        dump_messages = 0
        for record in log_manager.records:
            if record.getMessage().startswith('Dumping items to'):
                dump_messages += 1
        self.assertEqual(dump_messages, 2)

    def test_thread_manage_failed_normalizing_error(self):
        """Test logging in case of error during error management"""
        stream_normalizer = self.TestNormalizer().normalize_stream([])
        # causing an error by not initializing the stream normalizer
        # before calling _thread_manage_failed_normalizing
        with self.assertLogs(stream_normalizer.logger, level=logging.ERROR):
            stream_normalizer._thread_manage_failed_normalizing()

    def test_keyboard_interruption(self):
        """Test that keyboard interrupts are managed properly"""
        crawler = self.TestCrawler.from_kwargs()
        stream_normalizer = self.TestNormalizer().normalize_stream(crawler.crawl())
        mock_futures = (mock.Mock(), KeyboardInterrupt)
        with mock.patch('concurrent.futures.ThreadPoolExecutor.submit',
                        side_effect=mock_futures), \
             mock.patch('concurrent.futures.as_completed'):
            with self.assertLogs(normalizers.base.StreamMetadataNormalizer.logger,
                                 level=logging.DEBUG):
                iterator = iter(stream_normalizer)
                iterator.manager_thread.join()
            mock_futures[0].cancel.assert_called()

    def test_unexpected_error(self):
        """Test that unexpected errors (e.g. when starting a
        normalizing thread) are logged
        """
        stream_normalizer = self.TestNormalizer().normalize_stream([mock.Mock()])
        with mock.patch('concurrent.futures.ThreadPoolExecutor.submit',
                        side_effect=RuntimeError):
            with self.assertLogs(normalizers.base.StreamMetadataNormalizer.logger,
                                 level=logging.ERROR):
                iterator = iter(stream_normalizer)
                iterator.manager_thread.join()

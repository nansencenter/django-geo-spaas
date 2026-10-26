"""Tests for the recovery module"""
import logging
import tempfile
import unittest.mock as mock
from datetime import datetime
from pathlib import Path

import django.test
import requests

import geospaas.harvesting.crawlers.base as crawlers_base
import geospaas.harvesting.normalizers as normalizers
import geospaas.harvesting.recovery as recovery


class IngestionRecoveryTestCase(django.test.TestCase):
    """Tests for the ingestion recovery functions"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        mock.patch(
            'geospaas.harvesting.normalizers.base.StreamMetadataNormalizer.FAILED_INGESTIONS_PATH',
            self.tmp_dir.name
        ).start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        self.tmp_dir = None

    def generate_recovery_file(self, exception_type, errors_count=1):
        """Generate recovery file"""
        stream_normalizer = normalizers.StreamMetadataNormalizer(mock.MagicMock(), mock.MagicMock())
        to_pickle = [
            (crawlers_base.DatasetInfo(f'http://foo{i}'), exception_type(f'bar{i}'))
            for i in range(errors_count)
        ]
        date = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')
        # the assertion is just to remove the logs from the output
        with self.assertLogs(stream_normalizer.logger):
            stream_normalizer._pickle_list_elements(
                to_pickle, Path(self.tmp_dir.name, f"{date}_{stream_normalizer.RECOVERY_SUFFIX}"))

    def test_ingest_file(self):
        """Test ingesting a recovery file"""
        self.generate_recovery_file(requests.ConnectionError, errors_count=2)

        recovery_files = list(Path(self.tmp_dir.name).iterdir())
        if len(recovery_files) != 1:
            raise RuntimeError('One recovery file should have been generated')
        recovery_file = recovery_files[0]

        with mock.patch('geospaas.harvesting.ingesters.Ingester.ingest') as mock_ingest:
            with self.assertLogs(recovery.logger, level=logging.INFO):
                recovery.ingest_file(recovery_file)

        mock_ingest.assert_called_once_with([crawlers_base.DatasetInfo(f'http://foo{i}')
                                             for i in range(2)])
        self.assertFalse(recovery_file.exists())

    def test_ingest_file_nothing_to_ingest(self):
        """Test that no ingestion is triggered if the pickled exception
        are not of the supported types
        """
        self.generate_recovery_file(ValueError, errors_count=1)

        recovery_files = list(Path(self.tmp_dir.name).iterdir())
        if len(recovery_files) != 1:
            raise RuntimeError('One recovery file should have been generated')
        recovery_file = recovery_files[0]

        with mock.patch('geospaas.harvesting.ingesters.Ingester.ingest') as mock_ingest:
            with self.assertLogs(recovery.logger, level=logging.INFO):
                recovery.ingest_file(recovery_file)

        mock_ingest.assert_not_called()
        self.assertFalse(recovery_file.exists())

    def test_retry_ingest(self):
        """Test ingesting all recovery files in the failed ingestions
        folder
        """
        self.generate_recovery_file(requests.ConnectionError, errors_count=2)
        self.generate_recovery_file(requests.ConnectionError, errors_count=2)

        recovery_files = list(Path(self.tmp_dir.name).iterdir())
        if len(recovery_files) != 2:
            raise RuntimeError('Two recovery files should have been generated')

        with mock.patch('geospaas.harvesting.recovery.ingest_file') as mock_ingest_file:
            # remove recovery files, simulating a best case scenario
            mock_ingest_file.side_effect = lambda path: path.unlink()
            with self.assertLogs(recovery.logger, level=logging.INFO):
                recovery.retry_ingest()

        self.assertListEqual(
            mock_ingest_file.call_args_list,
            [mock.call(path) for path in recovery_files])

    def test_retry_ingest_with_failure(self):
        """Test ingesting all recovery files in the failed ingestions
        folder, with failures during the first re-ingestion
        """
        def generate_ingest_file_side_effect(test_case):
            """Returns a callable class which creates a recovery file
            the first time it is called. It also removes the file given
            as argument (not just the first time).
            """
            class Inner():
                def __init__(self, test_case):
                    self.test_case = test_case
                    self.called_once = False

                def __call__(self, file_path):
                    if not self.called_once:
                        self.test_case.generate_recovery_file(
                            requests.ConnectionError, errors_count=1)
                        self.called_once = True
                    file_path.unlink()
            return Inner(test_case)

        self.generate_recovery_file(requests.ConnectionError, errors_count=1)

        recovery_files = list(Path(self.tmp_dir.name).iterdir())
        if len(recovery_files) != 1:
            raise RuntimeError('One recovery file should have been generated')

        with mock.patch('geospaas.harvesting.recovery.ingest_file') as mock_ingest_file, \
                mock.patch('time.sleep') as mock_sleep:
            mock_ingest_file.side_effect = generate_ingest_file_side_effect(self)
            with self.assertLogs(recovery.logger):
                recovery.retry_ingest()

        # check that retry_ingest() has been called once with the first
        # recovery file, and once with the recovery file that was
        # generated when processing the first one
        self.assertEqual(len(mock_ingest_file.call_args_list), 2)
        self.assertTrue(all([
            call[1][0].name.endswith(normalizers.StreamMetadataNormalizer.RECOVERY_SUFFIX)
            for call in mock_ingest_file.mock_calls]))
        mock_sleep.assert_called_once_with(60)

    def test_retry_ingest_with_persistent_failure(self):
        """Test ingesting all recovery files in the failed ingestions
        folder, with persistent failures during re-ingestion resulting
        in files not being ingested
        """

        self.generate_recovery_file(requests.ConnectionError, errors_count=1)

        recovery_files = list(Path(self.tmp_dir.name).iterdir())
        if len(recovery_files) != 1:
            raise RuntimeError('One recovery file should have been generated')

        with mock.patch('geospaas.harvesting.recovery.ingest_file') as mock_ingest_file, \
                mock.patch('time.sleep') as mock_sleep:
            with self.assertLogs(recovery.logger):
                recovery.retry_ingest()

        # check that retry_ingest() has been called five times
        self.assertEqual(len(mock_ingest_file.call_args_list), 5)
        # check that the wait time increases for each failure
        # wait_times == (60, 60*2, 60*4, 60*8, ...)
        initial_wait_time = 60
        wait_times = (initial_wait_time * (2**i) for i in range(5))
        mock_sleep.assert_has_calls((mock.call(t) for t in wait_times))

    def test_retry_ingest_error(self):
        """Check that exception happening during re-ingestion of a file
        do not stop the re-ingestion process for other files
        """
        self.generate_recovery_file(requests.ConnectionError, errors_count=2)

        recovery_files = list(Path(self.tmp_dir.name).iterdir())
        if len(recovery_files) != 1:
            raise RuntimeError('One recovery file should have been generated')
        recovery_file = recovery_files[0]

        with mock.patch('geospaas.harvesting.recovery.ingest_file') as mock_ingest_file, \
                mock.patch('time.sleep'):
            mock_ingest_file.side_effect = RuntimeError
            with self.assertLogs(recovery.logger, level=logging.ERROR):
                recovery.retry_ingest()

        self.assertEqual(len(mock_ingest_file.mock_calls), 5)


class RecoveryTestCase(django.test.TestCase):
    """Tests for generic recovery functions"""
    def test_main(self):
        """Test that the recovery functions are called"""
        with mock.patch('geospaas.harvesting.recovery.retry_ingest') as mock_ingest:
            recovery.main()
        mock_ingest.assert_called_once()

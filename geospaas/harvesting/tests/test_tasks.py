"""Tests for the harvesting tasks"""

import unittest
import unittest.mock as mock

import geospaas.harvesting.tasks as tasks_harvesting


class StartHarvestTestCase(unittest.TestCase):
    """Tests for the start_harvest() task"""

    def setUp(self):
        self.mock_providers_config = mock.patch(
            'geospaas.harvesting.providers.ProvidersConfiguration').start()
        self.mock_search_config = mock.patch(
            'geospaas.harvesting.providers.SearchConfiguration').start()
        self.search_results_mocks = [mock.Mock(), mock.Mock()]
        (self.mock_search_config.from_dict.return_value
                                .create_provider_searches.return_value) = self.search_results_mocks
        self.mock_celery_group = mock.patch('celery.group').start()
        self.addCleanup(mock.patch.stopall)

    def test_start_harvest(self):
        """Test starting the harvesting process. This doesn't test
        much, improvements welcome
        """
        tasks_harvesting.start_harvest({'foo': 'bar'})
        self.assertListEqual(
            list(self.mock_celery_group.call_args[0][0]),
            [tasks_harvesting.save_search_results.s(search_result)
             for search_result in self.search_results_mocks])

class HarvestingTestCase(unittest.TestCase):
    """Tests for harvesting tasks"""

    def test_save_search_results(self):
        """Test saving search results"""
        mock_search_results = mock.Mock()
        tasks_harvesting.save_search_results(mock_search_results)
        mock_search_results.save.assert_called()

    def test_update_vocabularies(self):
        """Test updating vocabularies"""
        with mock.patch(
                'geospaas.harvesting.tasks.refresh_vocabularies') as mock_refresh:
            tasks_harvesting.update_vocabularies()
        mock_refresh.assert_called_with()

    def test_retry_ingestion(self):
        """Test retry_ingestion() task"""
        with mock.patch('geospaas.harvesting.tasks.retry_ingest') as mock_retry_ingest:
            tasks_harvesting.retry_ingestion()
        mock_retry_ingest.assert_called()

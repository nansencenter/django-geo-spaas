import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from geospaas.harvesting.crawlers.cmems import CMEMSCrawler
from geospaas.harvesting.crawlers.base import DatasetInfo


class TestCMEMSCrawler(unittest.TestCase):

    def setUp(self):
        """Set up a CMEMSCrawler instance for testing."""
        self.crawler = CMEMSCrawler(
            product_id="test_product",
            dataset_ids=["dataset_1", "dataset_2"],
            time_range=(datetime(2023, 1, 1), datetime(2023, 1, 31)),
            username="test_user",
            password="test_password"
        )

    def test_repr(self):
        """Test the __repr__ method."""
        expected_repr = ("CMEMSCrawler(product_id=test_product, "
                         "dataset_ids=['dataset_1', 'dataset_2'], "
                         "time_range=(datetime.datetime(2023, 1, 1, 0, 0), datetime.datetime(2023, 1, 31, 0, 0)), "
                         "username=test_user, password=******)")
        self.assertEqual(repr(self.crawler), expected_repr)

    def test_eq(self):
        """Test the __eq__ method."""
        other_crawler = CMEMSCrawler(
            product_id="test_product",
            dataset_ids=["dataset_1", "dataset_2"],
            time_range=(datetime(2023, 1, 1), datetime(2023, 1, 31)),
            username="test_user",
            password="test_password"
        )
        self.assertEqual(self.crawler, other_crawler)

    def test_make_filter(self):
        """Test making a regular expression matching a time range
        """
        mock_crawler = MagicMock()
        regex_template = "^(.*_({regex})_.*)|({regex}.*)$"

        mock_crawler.time_range = (datetime(2024, 9, 1),
                                   datetime(2024, 9, 2))
        self.assertEqual(
             CMEMSCrawler.make_filter(mock_crawler),
             regex_template.format(regex='(2024(09(01|02)))'))

        mock_crawler.time_range = (datetime(2024, 9, 1),
                                   datetime(2024, 10, 15))
        self.assertEqual(
             CMEMSCrawler.make_filter(mock_crawler),
             regex_template.format(regex=(
                 '(2024(09(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23'
                 '|24|25|26|27|28|29|30)|10(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15)))'
             )))

        mock_crawler.time_range = (datetime(2024, 11, 1),
                                   datetime(2025, 1, 1))
        self.assertEqual(
             CMEMSCrawler.make_filter(mock_crawler),
             regex_template.format(regex=(
                    '(202412[0-3][0-9])|(2024(11(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|'
                    '16|17|18|19|20|21|22|23|24|25|26|27|28|29|30)))|(2025(01(01)))')))

        mock_crawler.time_range = (datetime(2023, 12, 30),
                                   datetime(2024, 1, 2))
        self.assertEqual(
             CMEMSCrawler.make_filter(mock_crawler),
             regex_template.format(regex=('(2023(12(30|31)))|(2024(01(01|02)))')))

        mock_crawler.time_range = (datetime(2023, 12, 30),
                                   datetime(2025, 1, 2))
        self.assertEqual(
             CMEMSCrawler.make_filter(mock_crawler),
             regex_template.format(regex=(
                 '(2023(12(30|31)))|(2024[0-9]{4})|(2025(01(01|02)))')))

        mock_crawler.time_range = (None, None)
        self.assertIsNone(CMEMSCrawler.make_filter(mock_crawler))

    @patch("geospaas.harvesting.crawlers.cmems.copernicusmarine.describe")
    def test_set_initial_state(self, mock_describe):
        """Test the set_initial_state method."""
        mock_product = MagicMock()
        mock_product.products = [MagicMock()]
        mock_describe.return_value = mock_product

        self.crawler.set_initial_state()

        self.assertIsNotNone(self.crawler._product_info)
        mock_describe.assert_called_once_with(
            show_all_versions=False,
            product_id="test_product",
            disable_progress_bar=True
        )

    @patch("geospaas.harvesting.crawlers.cmems.copernicusmarine.get")
    @patch("geospaas.harvesting.crawlers.cmems.copernicusmarine.describe")
    def test_crawl(self, mock_describe, mock_get):
        """Test the crawl method."""
        mock_product = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.dataset_id = "dataset_1"
        mock_dataset.dataset_name = "Test Dataset"
        mock_dataset.versions = [MagicMock()]
        mock_dataset.versions[0].parts = [MagicMock()]
        mock_dataset.versions[0].parts[0].get_service_by_service_name.return_value.variables = [
            "var1", "var2"]
        mock_product.products = [MagicMock()]
        mock_product.products[0].datasets = [mock_dataset]
        mock_describe.return_value = mock_product

        mock_response = MagicMock()
        mock_response.files = [MagicMock()]
        mock_response.files[0].https_url = "https://example.com/file.nc"
        mock_get.return_value = mock_response

        results = list(self.crawler.crawl())

        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], DatasetInfo)
        self.assertEqual(results[0].url, "https://example.com/file.nc")
        self.assertEqual(results[0].metadata["cmems_dataset_name"], "Test Dataset")
        self.assertEqual(results[0].metadata["variables"], ["var1", "var2"])
        mock_get.assert_called_once_with(
            dataset_id="dataset_1",
            dry_run=True,
            regex=self.crawler.make_filter(),
            username="test_user",
            password="test_password",
            disable_progress_bar=True
        )

    @patch("geospaas.harvesting.crawlers.cmems.copernicusmarine.describe")
    def test_set_initial_state_no_product(self, mock_describe):
        """Test set_initial_state when no product is found."""
        mock_describe.return_value.products = []

        with self.assertRaises(RuntimeError) as context:
            self.crawler.set_initial_state()

        self.assertIn("No product found with ID: test_product", str(context.exception))

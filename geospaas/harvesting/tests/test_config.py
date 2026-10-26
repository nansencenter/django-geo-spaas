# pylint: disable=protected-access
"""Tests for the config module"""
import unittest
import unittest.mock as mock
import django.test

import geospaas.harvesting.config as config
from geospaas.harvesting.providers import Provider

from . import TEST_FILES_PATH


class ConfigurationTestCase(unittest.TestCase):
    """Tests for the Configuration class"""

    class TestConfiguration(config.Configuration):
        """Concrete configuration class used for testing"""
        config_arguments_parser = mock.Mock(parse=lambda d: d)

    def test_parse_config(self):
        """Test parsing configuration"""
        configuration = self.TestConfiguration()
        configuration._parse_config({'foo': 'bar', 'baz': 'qux'})
        self.assertEqual(configuration.foo, 'bar')
        self.assertEqual(configuration.baz, 'qux')

    def test_from_dict(self):
        """Test creating a configuration object from a dictionary"""
        configuration = self.TestConfiguration.from_dict({'foo': 'bar'})
        self.assertEqual(configuration.foo, 'bar')

    def test_from_file(self):
        """Test creating a configuration object from a YAML file"""
        configuration = self.TestConfiguration.from_file(TEST_FILES_PATH / 'sample.yml')
        self.assertEqual(configuration.foo, 'bar')


class ProvidersArgumentTestCase(django.test.TestCase):
    """Tests for the ProvidersArgument class"""

    def test_parse(self):
        """Test parsing a providers argument"""
        providers_arg = {
            'cmems': {
                'crawler': {
                    'name': 'cmems',
                    'username': 'user',
                    'password': 'pass',
                },
                'normalizer': {'name': 'cmems'}
            },
            'thredds': {
                'crawler': {'name': 'thredds'},
                'normalizer': {'max_threads': 30}
            }
        }
        parsed_providers = config.ProvidersArgument('providers').parse(providers_arg)
        self.assertListEqual(
            parsed_providers,
            [
                Provider(name='cmems', config={
                    'crawler': {
                        'name': 'cmems',
                        'username': 'user',
                        'password': 'pass',
                    },
                    'normalizer': {'name': 'cmems'},
                    'ingester': {},
                }),
                Provider(name='thredds', config={
                    'crawler': {'name': 'thredds'},
                    'normalizer': {'max_threads': 30},
                    'ingester': {},
                }),
            ])

    def test_parse_config_error(self):
        """Test error handling when parsing wrong configuration"""
        with self.assertRaises(ValueError):
            config.ProvidersArgument('providers').parse({'foo': {}})

    def test_parse_no_provider_found(self):
        """Test error handling when no crawler matches the requested
        type
        """
        with self.assertRaises(KeyError):
            config.ProvidersArgument('providers').parse({'foo': {'crawler': {'name': 'foo'}}})


class ProvidersConfigurationTestCase(django.test.TestCase):
    """Tests for the ProvidersConfiguration class"""

    def test_parse_providers_config(self):
        """Test parsing a providers configuration file"""
        with mock.patch('geospaas.harvesting.utils.http_request'):
            providers_config = config.ProvidersConfiguration.from_file(
                TEST_FILES_PATH / 'providers.yml')
            self.assertListEqual(
                providers_config.providers,
                [
                    Provider(
                        name='creodias',
                        config={
                            'crawler': {
                                'name': 'resto',
                                'url': 'https://datahub.creodias.eu',
                            },
                            'normalizer': {'name': 'resto'},
                            'ingester': {},
                         })
                ])


class GeneralConfigurationTestCase(unittest.TestCase):
    """Tests for the GeneralConfiguration class"""

    def test_parse_general_config(self):
        """Test parsing a general configuration file"""
        with mock.patch('geospaas.harvesting.utils.http_request'):
            providers_config = config.GeneralConfiguration.from_file(
                TEST_FILES_PATH / 'config.yml')
            self.assertFalse(providers_config.update_vocabularies)
            self.assertFalse(providers_config.update_vocabularies)
            self.assertDictEqual(providers_config.pythesint_versions, {'gcmd_instrument': '9.1.5'})


class SearchConfigurationTestCase(django.test.TestCase):
    """Tests for the SearchConfiguration class"""

    def setUp(self):
        self.mock_http_request = mock.patch('geospaas.harvesting.utils.http_request').start()
        self.addCleanup(mock.patch.stopall)
        self.search_config = (
            config.SearchConfiguration.from_file(TEST_FILES_PATH / 'search.yml'))
        # create testing providers
        for p in config.ProvidersConfiguration.from_file(TEST_FILES_PATH/'providers.yml').providers:
            p.save()

    def test_create_search_configuration(self):
        """Test making a SearchConfiguration object from files"""

        self.assertDictEqual(self.search_config.common, {})
        self.assertListEqual(self.search_config.searches, [{
            'provider_name': 'creodias',
            'crawler': {
                'collection': 'SENTINEL-3',
                'search_terms': {
                    'processingLevel': '2'
                },
                'start_time': '2023-01-01',
                'end_time': '2023-01-02',
            },
        }])

    def test_create_provider_searches(self):
        """Test starting searches from a SearchConfiguration object
        """
        with mock.patch('geospaas.harvesting.providers.Provider.search') as mock_search:
            self.assertListEqual(
                self.search_config.create_provider_searches(),
                [mock_search.return_value])
        mock_search.assert_called_once_with(
            crawler={
                'collection': 'SENTINEL-3',
                'search_terms': {'processingLevel': '2'},
                'start_time': '2023-01-01',
                'end_time': '2023-01-02'})

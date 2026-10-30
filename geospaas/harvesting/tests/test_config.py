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

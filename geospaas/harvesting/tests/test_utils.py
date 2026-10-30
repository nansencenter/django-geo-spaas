"""Tests for the geospaas.harvesting.utils module"""
import importlib
import io
import os
import unittest
import unittest.mock as mock
import xml.etree.ElementTree as ET

import geospaas.harvesting.utils as utils

class UtilsTestCase(unittest.TestCase):
    """Tests for utilities"""

    def test_should_strip_auth(self):
        """The authentication headers should be stripped if a
        redirection outside of the current domain happens
        """
        with utils.TrustDomainSession() as session:
            self.assertFalse(session.should_strip_auth('https://scihub.copernicus.eu/foo/bar',
                                                       'https://apihub.copernicus.eu/foo/bar'))

            self.assertFalse(session.should_strip_auth('https://scihub.copernicus.eu/foo/bar',
                                                       'https://scihub.copernicus.eu/baz'))

            self.assertFalse(session.should_strip_auth('http://scihub.copernicus.eu:80/foo/bar',
                                                       'https://scihub.copernicus.eu:443/foo/bar'))

            self.assertTrue(session.should_strip_auth('https://scihub.copernicus.eu/foo/bar',
                                                      'https://www.website.com/foo/bar'))

            self.assertTrue(session.should_strip_auth('https://scihub.copernicus.eu/foo/bar',
                                                      'https://foo.com/bar'))

    def test_http_request_with_auth(self):
        """If the `auth` argument is provided, the request should be
        executed inside a TrustDomainSession
        """
        with mock.patch('requests.Session.request', return_value='response') as mock_request:
            self.assertEqual(
                utils.http_request('GET', 'url', stream=False, auth=('username', 'password')),
                'response'
            )
            mock_request.assert_called_once_with('GET', 'url', stream=False)

    def test_http_request_without_auth(self):
        """If the `auth` argument is not provided, the request should
        simply be executed using requests.get()
        """
        with mock.patch('requests.request', return_value='response') as mock_request:
            self.assertEqual(
                utils.http_request('GET', 'url', stream=True),
                'response'
            )
            mock_request.assert_called_once_with('GET', 'url', stream=True)

    def test_yaml_parsing(self):
        """Test YAML parsing with environment variable retrieval"""
        yaml_content="""---
        foo: bar
        baz: !ENV ENV_VAR
        """
        buffer = io.StringIO(yaml_content)
        with mock.patch('builtins.open', return_value=buffer), \
             mock.patch('os.environ', {'ENV_VAR': 'qux'}):
            self.assertDictEqual(
                utils.read_yaml_file(''),
                {'foo': 'bar', 'baz': 'qux'})

    def test_xml_parsing(self):
        """Test XML parsing and namespaces extraction"""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
            <foo xml:lang="en" xmlns="http://bar/" xmlns:ns1="http://bar/ns1/">
                <ns1:baz attr='qux'/>
                <ns1:baz attr='quux'/>
            </foo>
        """
        xml_file = io.BytesIO(xml)
        tree, namespaces = utils.parse_xml_get_ns(xml_file)
        self.assertDictEqual(namespaces, {'default': 'http://bar/', 'ns1': 'http://bar/ns1/'})
        self.assertIsInstance(tree, ET.ElementTree)
        root = tree.getroot()
        self.assertEqual(root.tag, '{http://bar/}foo')
        self.assertEqual(len(list(root)), 2)

    def test_xml_parsing_error(self):
        """An exception must be raised if two namespaces have the same
        prefix
        """
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
            <foo xml:lang="en" xmlns="http://bar/" xmlns:ns1="http://bar/ns1/">
                <bar xmlns:ns1="http://baz/ns1/" />
            </foo>
        """
        xml_file = io.BytesIO(xml)
        with self.assertRaises(KeyError):
            _, _ = utils.parse_xml_get_ns(xml_file)

    def test_merge_configs(self):
        """Test merging dicts"""
        self.assertDictEqual(
            utils.merge_configs(config_dict={'a': 1, 'b': 2, 'c': {'d': 9}},
                                override={'a': 5, 'c': {'d': 8}, 'f': 0}),
            {'a': 5, 'b': 2, 'c': {'d': 8}, 'f': 0})

    def test_merge_configs_error(self):
        """An exception must be raised if the overridin"""
        with self.assertRaises(ValueError):
            utils.merge_configs(config_dict={'a': 1, 'b': 2, 'c': 3},
                                override={'a': 'foo', 'd': 0})


class SubclassesTestCase(unittest.TestCase):
    """Tests for utility functions dealing with subclasses"""

    class Base():
        """Base class for tests"""

    class A(Base):
        """Class for testing"""

    class B(Base):
        """Class for testing"""

    class C(B):
        """Class for testing"""

    class D(A, B):
        """Class for testing"""


    def test_get_all_subclasses(self):
        """Test that get_all_subclasses() returns all subclasses of
        the base class
        """
        self.assertEqual(
            utils.get_all_subclasses(self.Base),
            set((self.A, self.B, self.C, self.D)))

    def test_export_subclasses(self):
        """Test that export_subclasses imports the modules of the
        package and adds subclasses to __all__
        """
        # simulate the output of pkgutil.iter_modules()
        # see https://docs.python.org/3.7/library/pkgutil.html#pkgutil.iter_modules
        modules = (
            (mock.Mock(), 'module1', False),
            (mock.Mock(), 'module2', False)
        )
        with mock.patch.dict('sys.modules', {'package': mock.Mock()}):
            patched_utils = importlib.import_module('geospaas.harvesting.utils')
            with mock.patch('pkgutil.iter_modules', return_value=iter(modules)), \
                mock.patch('importlib.import_module'):
                package__all__ = []
                patched_utils.export_subclasses(
                    package__all__, 'package', '/foo/package', self.Base)
        self.assertCountEqual(package__all__, ['Base', 'A', 'B', 'C', 'D'])

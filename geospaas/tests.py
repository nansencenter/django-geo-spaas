import os
from mock import patch, PropertyMock

from django.test import TestCase

from geospaas.utils import utils

class TestUtils(TestCase):
    @patch('urllib3.PoolManager')
    def test_validate_uri_opendap_does_not_exist(self, mock_PoolManager):
        uri = 'http://www.ifremer.fr'
        mock_PoolManager.status=1
        with self.assertRaises(OSError) as cm:
            utils.validate_uri(uri)
        self.assertEqual('NetCDF: file not found', cm.exception.args[1])

    @patch('geospaas.utils.utils.os.path.isfile')
    def test_validate_uri_local(self, mock_isfile):
        mock_isfile.return_value = True
        uri = 'file://localhost/some/folder/filename.ext'
        self.assertEqual(utils.validate_uri(uri), None)

    def test_validate_uri_local_does_not_exist(self):
        uri = 'file://localhost/some/folder/filename.ext'
        with self.assertRaises(FileNotFoundError) as cm:
            utils.validate_uri(uri)
        the_exception = '/some/folder/filename.ext'
        self.assertEqual(the_exception, cm.exception.args[0])

    @patch('urllib3.PoolManager')
    def test__validate_uri__opendap_exists(self, mock_PoolManager):
        # Mock request.status so it returns 200, meaning successful connection..
        mock_PoolManager.return_value.request.return_value = PropertyMock(status=200)
        uri = 'http://nbstds.met.no/thredds/catalog/NBS/S2A/test_catalog.html'
        self.assertEqual(utils.validate_uri(uri), None)


    def test_fail_invalid_uri(self):
        uri = '/this/is/some/file/but/not/an/uri'
        with self.assertRaises(ValueError):
            utils.validate_uri(uri)

import unittest.mock as mock

from django.test import TestCase

from geospaas.utils import utils

class TestUtils(TestCase):

    def test_validate_uri_opendap_does_not_exist(self):
        uri = 'http://www.ifremer.fr/opendap/cerdap1/cersat/' \
              '20140101000000-GLOBCURRENT-L4-CURgeo_0m-ALT_OI-v02.0-fv01.0.nc.tull'
        with self.assertRaises(OSError) as cm:
            utils.validate_uri(uri)

    def test_validate_uri_local(self):
        with mock.patch('geospaas.utils.utils.os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            uri = 'file://localhost/some/folder/filename.ext'
            self.assertEqual(utils.validate_uri(uri), None)

    def test_validate_uri_local_does_not_exist(self):
        uri = 'file://localhost/some/folder/filename.ext'
        with self.assertRaises(FileNotFoundError) as cm:
            utils.validate_uri(uri)
        the_exception = '/some/folder/filename.ext'
        self.assertEqual(the_exception, cm.exception.args[0])

    def test_validate_uri__opendap_exists(self):
        with mock.patch('urllib.request.urlopen', return_value=mock.Mock(status=200)):
            uri = 'http://nbstds.met.no/thredds/catalog/NBS/S2A/test_catalog.html'
            self.assertIsNone(utils.validate_uri(uri))

    def test_validate_uri__opendap_http_not_200(self):
        """Test URI validation in case the HTTP response is not 200"""
        with mock.patch('urllib.request.urlopen', return_value=mock.Mock(status=300)):
            uri = 'http://foo/bar.nc'
            with mock.patch('netCDF4.Dataset') as mock_nc4_dataset:
                self.assertIsNone(utils.validate_uri(uri))
                mock_nc4_dataset.assert_called_with(uri)
            with mock.patch('netCDF4.Dataset', side_effect=(OSError, None)) as mock_nc4_dataset:
                self.assertIsNone(utils.validate_uri(uri))
                mock_nc4_dataset.assert_has_calls((
                    mock.call(uri),
                    mock.call(f"{uri}#fillmismatch")))

    def test_fail_invalid_uri(self):
        uri = '/this/is/some/file/but/not/an/uri'
        with self.assertRaises(ValueError):
            utils.validate_uri(uri)

    def test_nansat_filename(self):
        """Test the nansat_filename function"""
        self.assertEqual(utils.nansat_filename('file:///foo/bar.nc'), '/foo/bar.nc')
        self.assertEqual(utils.nansat_filename('https://foo/bar.nc'), 'https://foo/bar.nc')
        with mock.patch('urllib.request.urlretrieve', return_value=('/tmp/baz', None)):
            self.assertEqual(utils.nansat_filename('ftp://foo/bar.nc'), '/tmp/baz')

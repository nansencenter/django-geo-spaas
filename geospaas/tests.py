import os
from mock import patch, PropertyMock

from django.test import TestCase

from geospaas.utils import utils

class TestUtils(TestCase):

    def test_validate_uri_opendap_does_not_exist(self):
        uri = 'http://www.ifremer.fr/opendap/cerdap1/globcurrent/' \
                'v2.0/global_012_deg/geostrophic/2014/001/' \
                '20140101000000-GLOBCURRENT-L4-CURgeo_0m-ALT_OI-v02.0-fv01.0.nc.tull'
        with self.assertRaises(OSError) as cm:
            utils.validate_uri(uri)
        self.assertEqual('NetCDF: file not found', cm.exception.args[1])

    @patch('os.path.isfile')
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

    @patch('geospaas.utils.utils.os.mkdir')
    def test_module_path(self, mock_mkdir):
        mock_mkdir.return_value = None
        module = 'geospaas.catalog'
        root = '/home/vagrant/site_media/media'
        mpath = utils.module_path(module, root)
        self.assertEqual(mpath, os.path.join(root, 'geospaas/catalog'))

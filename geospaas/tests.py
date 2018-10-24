import os
from mock import patch

from django.test import TestCase

from geospaas.utils import utils

class TestUtils(TestCase):

    def test_validate_uri_opendap(self):
        uri = 'http://www.ifremer.fr/opendap/cerdap1/globcurrent/' \
                'v2.0/global_012_deg/geostrophic/2014/001/' \
                '20140101000000-GLOBCURRENT-L4-CURgeo_0m-ALT_OI-v02.0-fv01.0.nc'
        self.assertTrue(utils.validate_uri(uri))

    def test_validate_uri_opendap_does_not_exist(self):
        uri = 'http://www.ifremer.fr/opendap/cerdap1/globcurrent/' \
                'v2.0/global_012_deg/geostrophic/2014/001/' \
                '20140101000000-GLOBCURRENT-L4-CURgeo_0m-ALT_OI-v02.0-fv01.0.nc.tull'
        self.assertFalse(utils.validate_uri(uri))

    @patch('os.path.isfile')
    def test_validate_uri_local(self, mock_isfile):
        mock_isfile.return_value = True
        uri = 'file://localhost/some/folder/filename.ext'
        self.assertTrue(utils.validate_uri(uri))

    def test_validate_uri_local_does_not_exist(self):
        uri = 'file://localhost/some/folder/filename.ext'
        self.assertFalse(utils.validate_uri(uri))

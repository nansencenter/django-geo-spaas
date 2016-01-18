import os
from django.conf import settings
from django.test import TestCase

from nansencloud.viewer import tools as vtools

class TestViewer(TestCase):

    def test_media_path(self):

        f = '/mnt/10.11.12.232/sat_downloads_asar/level-0/gsar_rvl/' \
                'RVL_ASA_WS_20091116195940116.gsar'
        media_path = vtools.media_path('nansencloud.processing_sar_doppler', f)
        self.assertTrue(os.path.exists(media_path))
        self.assertEqual(media_path, os.path.join(settings.MEDIA_ROOT,
            'nansencloud', 'processing_sar_doppler',
            'RVL_ASA_WS_20091116195940116'))

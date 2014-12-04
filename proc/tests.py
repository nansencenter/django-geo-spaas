import os
import glob

import datetime
from django.test import TestCase
from django.contrib.gis.geos import Polygon

from cat.models import *
from proc.models import *

idir = '/Data/sat/downloads/'
ifiles = glob.glob(os.path.join(idir, 'MERIS', 'MER_FRS_1*N1'))

class ChainModelTests(TestCase):
    def test_create_chain(self):
        ''' should create a hain '''
        ch = Chain.objects.get_or_create(
            name='MerisWeb',
            webname='MERIS',
            description = '''
            Simple processing of MERIS inluding only quick look production
            '''
            )[0]

        ch.full_clean()

class ProcSearchModelTests(TestCase):
    def test_init(self):
        ch = Chain.objects.get_or_create(
            name='MerisWeb',
            webname='MERIS',
            description = '''
            Simple processing of MERIS inluding only quick look production
            '''
            )[0]

        ps = ProcSearch(chain=ch,
                        sdate=datetime.datetime.now(),
                        date0=datetime.datetime.now(),
                        date1=datetime.datetime.now(),
                        polygon=None)
        ps.full_clean()


    def test_init_empty(self):

        ps = ProcSearch(sdate=datetime.datetime.now(),
                        date0=datetime.datetime.now(),
                        date1=datetime.datetime.now())
        ps.full_clean()
        ps.save()

class MerisWebModelTests(TestCase):

    def test_create_from_image(self):
        ''' should create MerisWeb from Image instance
        all Image attributes should be awailable with MerisWeb + more'''
        # create image instance
        i = Image.objects.get_or_create(ifiles[0])[0]
        i.save()

        # create MerisWeb from image
        mw = MerisWeb.create(i)[0]

        self.assertEqual(mw.image.id, i.id)
        self.assertEqual(mw.sourcefile, i.sourcefile)

    def test_create_from_filename(self):
        ''' should create MerisWeb  from filename '''

        filename = ifiles[0]
        im = Image.objects.get_or_create(filename)[0]
        im.save()

        # Now check that a MerisWeb instance can be created the same way,
        # automatically using the correct image and not creating a new one
        mw = MerisWeb.create(filename)[0]

        self.assertEqual(mw.image.id, im.id)

    def test_create_set_and_save(self):
        ''' Should create MerisWeb instance, set attrs and save'''
        m1, cr1 = MerisWeb.create(ifiles[0])

        m1.resolution = 'FR'
        m1.level =      '1'
        m1.quicklook = SourceFile.objects.get_or_create(ifiles[0])[0]
        m1.daily = True
        m1.chain = MerisWeb.get_chain()

        m1.save()

    def test_create_returns_correct_creation_status(self):
        m1, cr1 = MerisWeb.create(ifiles[0])

        m1.resolution = 'FR'
        m1.level =      '1'
        m1.quicklook = SourceFile.objects.get_or_create(ifiles[0])[0]
        m1.daily = True
        m1.chain = MerisWeb.get_chain()

        m1.save()

        m2, cr2 = MerisWeb.create(ifiles[0])

        self.assertEqual(cr1, True)
        self.assertEqual(cr2, False)

    def test_get_chain(self):
        ''' should create Chain'''
        ch = MerisWeb.get_chain()
        ch.full_clean()

    def test_process(self):
        """
        should run processing of an existing image and set all params
        """
        mw = MerisWeb.create(ifiles[0])[0]
        mw.process(opts={'odir': './',
                          'url': 'http://web.nersc.no/project/maires/catalog/meris/'})
        mw.full_clean()
        mw.save()

class SARWebModelTests(TestCase):

    def test_process_rs2(self):
        rs2 = SARWeb.create('/Data/sat/downloads/Radarsat2/' \
                'RS2_20140924_053636_0076_SCWA_HHHV_SGF_349932_5397_10107007.zip'
                )[0]
        rs2.process()
        rs2.full_clean()
        rs2.save()

        self.assertIsInstance(SARWeb.objects.get(quicklooks__name =
                u'RS2_20140924_053636_0076_SCWA_HHHV_SGF_349932_5397_10107007_HH.png'),
                SARWeb)

    def test_process_s1a(self):
        s1a = SARWeb.create('/Data/sat/downloads/Sentinel-1/' \
                'S1A_EW_GRDH_1SDH_20140902T170622_20140902T170652_002216_002424_A944.zip'
                )[0]
        s1a.process()
        s1a.full_clean()
        s1a.save()

        self.assertIsInstance(SARWeb.objects.get(quicklooks__name =
                u'S1A_EW_GRDH_1SDH_20140902T170622_20140902T170652_002216_002424_A944_HH.png'),
                SARWeb)

    def test_process_asar(self):
        a = SARWeb.create(
            '/Data/sat/downloads/ASAR/benguela/' \
            'ASA_WSM_1PNPDE20080818_210658_000002142071_00200_33821_6341.N1'
            )[0]
        a.process()
        a.full_clean()
        a.save()

        self.assertIsInstance(SARWeb.objects.get(quicklooks__name =
                u'ASA_WSM_1PNPDE20080818_210658_000002142071_00200_33821_6341_VV.png'),
                SARWeb)


import os, glob
import datetime
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.gis.geos import Polygon

from django.core.exceptions import ValidationError

from django.core.management import call_command
from django.utils.six import StringIO

from nansat import *

from nansencloud.cat.models import *
from nansencloud.cat.forms import SearchForm

ifiles = glob.glob(os.path.join('/Data/sat/downloads/MERIS', 'MER_FRS_*N1'))
if not ifiles:
    raise Exception('Folder /Data/sat/downloads/MERIS not mounted')

class AddImagesTests(TestCase):
    def test_add_images_command_filenames(self):
        out = StringIO()
        call_command('add_images', ifiles[0], ifiles[1], stdout=out)
        self.assertIn('Successfully added satellite image: %s'%ifiles[0],
                out.getvalue())
        self.assertIn('Successfully added satellite image: %s'%ifiles[1],
                out.getvalue())

    def test_add_images_command_foldernames(self):
        out = StringIO()
        p1 = '/Data/sat/downloads/ASAR/miscellaneous'
        p2 = '/Data/sat/downloads/ASAR/ligurian'
        call_command('add_images', p2,p1, stdout=out)
        output = out.getvalue()
        self.assertIn('Successfully added satellite images:',
                output)
        self.assertIn('%s'%p1, output)
        self.assertIn('%s'%p2, output)

    #def test_add_images_ufunc(self):


class SourceFileTests(TestCase):
    def test_create(self):
        ''' should create SourceFile from full path and set all attributes '''
        fullpath = ifiles[0]
        path, name = os.path.split(fullpath)
        sf1, cr1 = SourceFile.objects.get_or_create(fullpath)

        self.assertEqual(str(sf1), str(fullpath))
        self.assertEqual(str(sf1.name), name)
        self.assertEqual(str(sf1.path.address), path)
        self.assertEqual(cr1, True)

    def test_force_create(self):
        ''' should create sourcefile from non existing file '''
        sf1, cr1 = SourceFile.objects.get_or_create('/wrong/path/file.png',
                                                    force=True)

        self.assertEqual(cr1, True)

class LocationTests(TestCase):
    def test_create(self):
        path1 = '/some/data/path'

        # use custom manager
        sf1, cr1 = Location.objects.get_or_create(path1)

        # use models.Manager
        sf2, cr2 = Location.objects.get_or_create(address=path1)

        self.assertEqual(str(sf1), path1)
        self.assertEqual(str(sf1.address), path1)
        self.assertEqual((cr1, cr2), (True, False))


class SensorManagerTests(TestCase):
    def test_dont_create_duplicate(self):
        ''' should create only one instance from 'MERIS' '''
        sen = Sensor.objects.get_or_create(name='MERIS')[0]
        sen = Sensor.objects.get_or_create(name='MERIS')[0]

        sens = Sensor.objects.all()
        self.assertEqual(len(sens), 1)


class SensorModelTests(TestCase):
    def test_capitalize(self):
        """ should create, save and delete 'MERIS/ENVISAT' """
        sen = Sensor.objects.get_or_create(name='MERIS')[0]
        self.assertEqual(str(sen), 'Meris')


class SatelliteModelTests(TestCase):
    def test_capitalize(self):
        """ should create, save and keep 'ENVISAT' """
        s0, cr = Satellite.objects.get_or_create(name='ENVISAT')
        self.assertEqual(str(s0), 'Envisat')


class ImageManagerTests(TestCase):
    def test_get_or_create(self):
        ''' Should create an image and save'''
        i, cr = Image.objects.get_or_create(ifiles[0], mapper='meris_l1')
        self.assertEqual(cr, True)

    def test_sourcefiles(self):
        ''' Should return list of filenames '''
        # create 2 images
        image, cr = Image.objects.get_or_create(ifiles[0], mapper='meris_l1')
        image, cr = Image.objects.get_or_create(ifiles[1], mapper='meris_l1')
        # get their filenames
        sourcefiles = Image.objects.sourcefiles()

        self.assertEqual(len(sourcefiles), 2)
        self.assertEqual(sourcefiles[0], ifiles[0])
        self.assertEqual(sourcefiles[1], ifiles[1])

    def test_new_sourcefiles(self):
        ''' Should return list of sourcefiles '''
        # create 3 images
        image, cr = Image.objects.get_or_create(ifiles[0], mapper='meris_l1')
        image, cr = Image.objects.get_or_create(ifiles[1], mapper='meris_l1')
        image, cr = Image.objects.get_or_create(ifiles[2], mapper='meris_l1')
        # get their filenames
        sourcefiles = Image.objects.sourcefiles()
        # get delta between database and files on disk
        new_sourcefiles = Image.objects.new_sourcefiles(ifiles)

        self.assertTrue(len(new_sourcefiles) > 0)
        self.assertTrue(sourcefiles[0] not in new_sourcefiles)
        self.assertTrue(sourcefiles[1] not in new_sourcefiles)
        self.assertTrue(sourcefiles[2] not in new_sourcefiles)

    def test_all_params_saved(self):
        i1, cr = Image.objects.get_or_create(ifiles[0])

        fname = os.path.split(ifiles[0])[1]
        i2 = Image.objects.get(sourcefile__name = fname)

        self.assertIsNotNone(i2.sourcefile)
        self.assertIsNotNone(i2.sensor)
        self.assertIsNotNone(i2.satellite)
        self.assertIsNotNone(i2.start_date)
        self.assertIsNotNone(i2.stop_date)
        self.assertIsNotNone(i2.mapper)

        self.assertEqual(i2.status.status, Status.GOOD_STATUS)

    def test_bad_nansat_file(self):
        ''' SHould create bad status for non openable image '''
        i, cr = Image.objects.get_or_create(
            '/Data/sat/downloads/Sentinel-1/S1A_IW_GRDH_1SDH_20140820T064001_20140820T064026_002020_001F56_8F1B.zip')
        self.assertEqual(i.status.status, Status.BAD_STATUS)

    def test_dont_create_from_bad_full_path(self):
        """ should not  open image with nansat from bad location """
        with self.assertRaises(IOError):
            i = Image.objects.get_or_create('/Da/s/dloads/ME/MER_0712_000001012008_00395_02453_1321.N1')

    def test_dont_create_duplicate(self):
        """ should not create two equal entries """
        i0, cr0 = Image.objects.get_or_create(ifiles[0])
        i1, cr1 = Image.objects.get_or_create(ifiles[0])
        self.assertEqual((cr0, cr1), (True, False))


class ImageModelTests(TestCase):
    def test_dont_get_not_existing(self):
        sf = SourceFile.objects.get_or_create(ifiles[0])[0]
        with self.assertRaises(Image.DoesNotExist):
            image = Image.objects.get(sourcefile=sf)

    def test_dont_save_empty(self):
        """ Should not save without filename """
        i = Image()
        with self.assertRaises(ValidationError):
            i.save()

    def test_border2leaflet(self):
        ''' border2leaflet() should return valid javascript'''
        i0 = Image.objects.get_or_create(ifiles[0])[0]
        print i0.border2str()

    def test_get_bands(self):
        ''' Should get all global metedata from the file '''
        i0 = Image.objects.get_or_create(ifiles[0])[0]
        bands = i0.bands.all()
        print bands[0], '\n\n'

        self.assertTrue(len(bands) > 0)


class StatusModelTests(TestCase):
    def test_create_status(self):
        status = Status.objects.get_or_create(status=Status.GOOD_STATUS, message='OK!')[0]
        status.save()

        self.assertEqual(status.status, 0)


class SearchTests(TestCase):
    def setUp(self):
        self.sdate      = datetime.datetime.today()
        self.date0      = datetime.date.today()-datetime.timedelta(10)
        self.date1      = datetime.date.today()
        self.polygon    = Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0)))
        self.status    = Status.objects.get_or_create(status=0, message='OK!')[0]
        self.satellite = Satellite.objects.get_or_create(name='ENVISAT')[0]
        self.sensor    = Sensor.objects.get_or_create(name='MERIS')[0]


class SearchModelTests(SearchTests):
    def test_create_search(self):
        ''' Should create valid Search instance '''
        s = Search(sdate=self.sdate,
                   date0=self.date0,
                   date1=self.date1,
                   polygon=self.polygon,
                   status=self.status,
                   satellite=self.satellite,
                   sensor=self.sensor
                )
        s.save()

        self.assertEqual(s.sdate.date(), datetime.datetime.today().date())
        self.assertEqual(s.status.status, 0)
        self.assertEqual(s.satellite.name, 'Envisat')
        self.assertEqual(s.sensor.name, 'Meris')


class SearchFormTests(SearchTests):
    def test_create_valid_minimal(self):
        ''' Should create form instance with valid data'''
        data = {'date0': self.date0,
                'date1': self.date1,
                    }

        form = SearchForm(data)
        self.assertEqual(form.is_valid(), True)

    def test_create_valid_full(self):
        ''' Should create form instance with valid data'''
        data = {'sdate':     self.sdate,
                'date0':     self.date0,
                'date1':     self.date1,
                'polygon':   self.polygon,
                'status':    self.status.id,
                'satellite': self.satellite.id,
                'sensor':    self.sensor.id,
                    }

        form = SearchForm(data)
        self.assertEqual(form.is_valid(), True)
        print form.errors

    def test_dont_create_invalid_date0(self):
        ''' Should create form instance with valid data'''
        data = {'date0': 1,
                'date1': datetime.date.today(),
                'polygon': Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0))),
                }
        form = SearchForm(data)
        self.assertEqual(form.is_valid(), False)

    def test_dont_create_invalid_polygon(self):
        ''' Should create form instance with valid data'''
        data = {'date0': 1,
                'date1': datetime.date.today(),
                'polygon': 'some crap',
                }
        form = SearchForm(data)
        self.assertEqual(form.is_valid(), False)

    def test_dont_create_empty(self):
        ''' Should create form instance with valid data'''
        form = SearchForm({})
        self.assertEqual(form.is_valid(), False)


class BandModelTests(TestCase):
    def test_create_band(self):
        ''' Should create a Band instance '''
        n = Nansat(ifiles[0])
        nBands = n.bands()

        bandNumber = 1
        fullpath = nBands[bandNumber]['SourceFilename']

        sourcefile = SourceFile.objects.get_or_create(fullpath)[0]
        sourceband = int(nBands[bandNumber]['SourceBand'])
        name = nBands[bandNumber].get('name', 'unknown')
        standard_name = nBands[bandNumber].get('standard_name', 'unknown')

        band = Band(sourcefile=sourcefile,
                    sourceband=sourceband,
                    name=name,
                    standard_name=standard_name)
        band.save()

    def test_get_array(self):
        ''' should get non empty numpy array from band '''
        i = Image.objects.get_or_create(ifiles[0])[0]
        b = i.bands.all()[0]
        array = b.get_data()

        self.assertEqual(type(array), np.ndarray)
        self.assertTrue(array.shape[0] > 0)
        self.assertTrue(array.shape[1] > 0)

    def test_get_image(self):
        ''' should get Pillow Image object '''
        i = Image.objects.get_or_create(ifiles[0])[0]
        b = i.bands.all()[0]
        img = b.get_image()
        img.save('test.png')

        self.assertTrue(os.path.exists('test.png'))
        os.remove('test.png')


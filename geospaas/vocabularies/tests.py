from mock.mock import MagicMock, patch

from django.test import TestCase
from django.core.management import call_command


from geospaas.vocabularies.models import Parameter
from geospaas.vocabularies.models import DataCenter
from geospaas.vocabularies.models import HorizontalDataResolution
from geospaas.vocabularies.models import Instrument
from geospaas.vocabularies.models import ISOTopicCategory
from geospaas.vocabularies.models import Location
from geospaas.vocabularies.models import Platform
from geospaas.vocabularies.models import Project
from geospaas.vocabularies.models import ScienceKeyword
from geospaas.vocabularies.models import TemporalDataResolution
from geospaas.vocabularies.models import VerticalDataResolution


class VocabulariesTestBase(object):
    fixtures = ["vocabularies"]
    def setUp(self):
        self.patcher = patch('geospaas.vocabularies.managers.print')
        self.mock_print = self.patcher.start()
        self.model.objects.update = MagicMock(return_value=None)
        self.model.objects.get_list = MagicMock(return_value=self.model_list)

    def tearDown(self):
        self.patcher.stop()

    def test_create_from_vocabularies(self):
        """ Test shared with all vocabularies """
        self.model.objects.create_from_vocabularies(force=True)
        self.model.objects.create_from_vocabularies()
        self.model.objects.get_list.assert_called()
        self.model.objects.update.assert_called()
        self.assertIn('Successfully added', self.mock_print.call_args[0][0])


class ParameterTests(VocabulariesTestBase, TestCase):
    model = Parameter
    model_list = [{'standard_name': 'surface_radial_doppler_sea_water_velocity', 'long_name': 'Radial Doppler Current', 'short_name': 'Ur', 'units': 'm s-1', 'minmax': '-1 1', 'colormap': 'jet'}]
    model.objects.update2 = MagicMock(return_value=None)
    model.objects.get_list2 = MagicMock(return_value=[])

    def test_get_parameter(self):
        p = Parameter.objects.get(standard_name='surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity')
        self.assertEqual(p.units, 'Hz')

    def test_get_or_create(self):
        dc0 = Parameter.objects.get(standard_name='surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity')
        dc1 = dict(
                standard_name=dc0.standard_name,
                short_name=dc0.short_name,
                units=dc0.units)
        dc2, cr = Parameter.objects.get_or_create(dc1)
        self.assertEqual(dc0, dc2)
        self.assertFalse(cr)


class DataCenterTests(VocabulariesTestBase, TestCase):
    model = DataCenter
    model_list = [{'Bucket_Level0': 'ACADEMIC', 'Bucket_Level1': 'OR-STATE/EOARC', 'Bucket_Level2': '', 'Bucket_Level3': '', 'Short_Name': 'OR-STATE/EOARC', 'Long_Name': 'Eastern Oregon Agriculture Research Center, Oregon State University', 'Data_Center_URL': 'http://oregonstate.edu/dept/eoarcunion/'}]

    def test_get_datacenter(self):
        dc = DataCenter.objects.get(short_name='NERSC')
        # OBS: Note error in the long name - they have been notified and this
        # test should fail at some point...
        self.assertEqual(dc.long_name, 'Nansen Environmental and Remote Sensing Centre')

    def test_get_or_create(self):
        dc0 = DataCenter.objects.get(short_name='NERSC')
        dc1 = dict(
                Bucket_Level0=dc0.bucket_level0,
                Bucket_Level1=dc0.bucket_level1,
                Bucket_Level2=dc0.bucket_level2,
                Bucket_Level3=dc0.bucket_level3,
                Short_Name=dc0.short_name,
                Long_Name=dc0.long_name,
                Data_Center_URL=dc0.data_center_url)
        dc2, cr = DataCenter.objects.get_or_create(dc1)
        self.assertEqual(dc0, dc2)
        self.assertFalse(cr)


class InstrumentTests(VocabulariesTestBase, TestCase):
    model = Instrument
    model_list = [{'Category': 'Earth Remote Sensing Instruments', 'Class': 'Active Remote Sensing', 'Type': 'Altimeters', 'Subtype': 'Lidar/Laser Altimeters', 'Short_Name': 'AIRBORNE LASER SCANNER', 'Long_Name': ''}]

    def test_get_instrument(self):
        ii = Instrument.objects.get(short_name='ASAR')
        self.assertEqual(ii.long_name, 'Advanced Synthetic Aperature Radar')

    def test_get_or_create(self):
        i0 = Instrument.objects.get(short_name='ASAR')
        i1 = dict(
            Category=i0.category,
            Class=i0.instrument_class,
            Type=i0.type,
            Subtype=i0.subtype,
            Short_Name=i0.short_name,
            Long_Name=i0.long_name)
        i2, cr = Instrument.objects.get_or_create(i1)
        self.assertEqual(i0, i2)
        self.assertFalse(cr)


class ISOTopicCategoryTests(VocabulariesTestBase, TestCase):
    model = ISOTopicCategory
    model_list = [{'iso_topic_category': 'Biota'}]

    def test_get_iso_category(self):
        cat = ISOTopicCategory.objects.get(name='Oceans')
        self.assertEqual(cat.name, 'Oceans')

    def test_get_or_create(self):
        iso0 = ISOTopicCategory.objects.get(name='Oceans')
        iso1 = dict(iso_topic_category=iso0.name)
        iso2, cr = ISOTopicCategory.objects.get_or_create(iso1)
        self.assertEqual(iso0, iso2)
        self.assertFalse(cr)


class LocationTests(VocabulariesTestBase, TestCase):
    model = Location
    model_list = [{'Location_Category': 'CONTINENT', 'Location_Type': 'AFRICA', 'Location_Subregion1': 'CENTRAL AFRICA', 'Location_Subregion2': 'ANGOLA', 'Location_Subregion3': ''}]

    def test_get_location(self):
        loc = Location.objects.get(subregion2='KENYA')
        self.assertEqual(loc.type, 'AFRICA')

    def test_get_or_create(self):
        loc0 = Location.objects.get(subregion2='KENYA')
        loc1 = dict(
                Location_Category=loc0.category,
                Location_Type=loc0.type,
                Location_Subregion1=loc0.subregion1,
                Location_Subregion2=loc0.subregion2,
                Location_Subregion3=loc0.subregion3)
        loc2, cr = Location.objects.get_or_create(loc1)
        self.assertEqual(loc0, loc2)
        self.assertFalse(cr)


class PlatformTests(VocabulariesTestBase, TestCase):
    model = Platform
    model_list = [{'Category': 'Aircraft','Series_Entity': '','Short_Name': 'A340-600','Long_Name': 'Airbus A340-600'}]

    def test_get_platform(self):
        p = self.model.objects.get(short_name='ENVISAT')
        self.assertEqual(p.category, 'Earth Observation Satellites')

    def test_get_or_create(self):
        p0 = self.model.objects.get(short_name='ENVISAT')
        p1 = dict(
                Category=p0.category,
                Series_Entity=p0.series_entity,
                Short_Name=p0.short_name,
                Long_Name=p0.long_name)
        p2, cr = Platform.objects.get_or_create(p1)
        self.assertEqual(p0, p2)
        self.assertFalse(cr)


class ProjectTests(VocabulariesTestBase, TestCase):
    model = Project
    model_list = [{'Bucket': 'A - C', 'Short_Name': 'AAE', 'Long_Name': 'Australasian Antarctic Expedition of 1911-14'}]

    def test_get_project(self):
        p = self.model.objects.get(short_name='ACSOE')
        self.assertEqual(p.long_name,
            'Atmospheric Chemistry Studies in the Oceanic Environment')


class ScienceKeywordTests(VocabulariesTestBase, TestCase):
    model = ScienceKeyword
    model_list = [{'Category': 'EARTH SCIENCE SERVICES', 'Topic': 'DATA ANALYSIS AND VISUALIZATION', 'Term': 'CALIBRATION/VALIDATION', 'Variable_Level_1': 'CALIBRATION', 'Variable_Level_2': '', 'Variable_Level_3': '', 'Detailed_Variable': ''}]

    def test_get_science_keyword(self):
        kw = self.model.objects.get(variable_level_1='SIGMA NAUGHT')
        self.assertEqual(kw.topic, 'SPECTRAL/ENGINEERING')


class TemporalDataResolutionTests(VocabulariesTestBase, TestCase):
    model = TemporalDataResolution
    model_list = [{'Temporal_Resolution_Range': '1 minute - < 1 hour'}]

    def test_get_temporal_range(self):
        tr = self.model.objects.get(range='1 minute - < 1 hour')
        self.assertEqual(tr.range, '1 minute - < 1 hour')


class HorizontalDataResolutionTests(VocabulariesTestBase, TestCase):
    model = HorizontalDataResolution
    model_list = [{'Horizontal_Resolution_Range': '1 km - < 10 km or approximately .01 degree - < .09 degree'}]

    def test_get_horizontal_range(self):
        rr = self.model.objects.get(range='< 1 meter')
        self.assertEqual(rr.range, '< 1 meter')


class VerticalDataResolutionTests(VocabulariesTestBase, TestCase):
    model = VerticalDataResolution
    model_list = [{'Vertical_Resolution_Range': '1 meter - < 10 meters'}]

    def test_get_vertical_range(self):
        vr = self.model.objects.get(range='10 meters - < 30 meters')
        self.assertEqual(vr.range, '10 meters - < 30 meters')


class CommandsTests(TestCase):
    def setUp(self):
        return_value=[{'Revision': '2019-02-13 08:48:55'}]
        models = [
            Parameter,
            DataCenter,
            HorizontalDataResolution,
            Instrument,
            ISOTopicCategory,
            Location,
            Platform,
            Project,
            ScienceKeyword,
            TemporalDataResolution,
            VerticalDataResolution,
            ]
        # mock get_list in all managers
        self.get_list_mocks = [
            patch.object(model.objects, 'get_list', return_value=return_value).start()
            for model in models]
        # mock update in all managers
        self.update_mocks = [
            patch.object(model.objects, 'update', return_value=return_value).start()
            for model in models]

    def test_command_update_vocabularies(self):
        call_command('update_vocabularies')
        # check that get_list was called only once
        for mock in self.get_list_mocks:
            mock.assert_called()
        # check that update was never called
        for mock in self.update_mocks:
            mock.assert_not_called()

    def test_command_update_vocabularies_force(self):
        call_command('update_vocabularies', '--force')
        # check that get_list was called only once
        for mock in self.get_list_mocks:
            mock.assert_called()
        # check that update was never called
        for mock in self.update_mocks:
            mock.assert_called()

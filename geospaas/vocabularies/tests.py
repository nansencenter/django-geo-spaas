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

class BaseForVocabulariesTests(TestCase):
    fixtures = ["vocabularies"]
    def setUp(self):
        self.patcher = patch('geospaas.vocabularies.managers.pti')
        self.mock_pti = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()


class ParameterTests(BaseForVocabulariesTests):
    ''' This is probably not needed as it should be covered by the
    DatasetParameterTests
    '''
    def test_get_or_create(self):
        p0 = Parameter.objects.first()
        p1 = dict(standard_name=p0.standard_name,
                   short_name=p0.short_name,
                   units=p0.units)
        p2, cr = Parameter.objects.get_or_create(p1)
        self.assertEqual(p0, p2)
        self.assertFalse(cr)


class DataCenterTests(BaseForVocabulariesTests):
    def test_get_datacenter(self):
        dc = DataCenter.objects.get(short_name='NERSC')
        # OBS: Note error in the long name - they have been notified and this
        # test should fail at some point...
        self.assertEqual(dc.long_name, 'Nansen Environmental and Remote Sensing Centre')

    def test_create_from_vocabularies(self):
        DataCenter.objects.create_from_vocabularies()
        self.mock_pti.update_gcmd_provider.assert_called_once()
        self.mock_pti.get_gcmd_provider_list.assert_called_once()

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


class HorizontalDataResolutionTests(BaseForVocabulariesTests):
    def test_get_horizontal_range(self):
        rr = HorizontalDataResolution.objects.get(range='< 1 meter')
        self.assertEqual(rr.range, '< 1 meter')


class InstrumentTests(BaseForVocabulariesTests):
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


class ISOTopicCategoryTests(BaseForVocabulariesTests):
    def test_get_iso_category(self):
        cat = ISOTopicCategory.objects.get(name='Oceans')
        self.assertEqual(cat.name, 'Oceans')

    def test_get_or_create(self):
        iso0 = ISOTopicCategory.objects.get(name='Oceans')
        iso1 = dict(iso_topic_category=iso0.name)
        iso2, cr = ISOTopicCategory.objects.get_or_create(iso1)
        self.assertEqual(iso0, iso2)
        self.assertFalse(cr)


class LocationTests(BaseForVocabulariesTests):
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


class PlatformTests(BaseForVocabulariesTests):
    def test_get_platform(self):
        p = Platform.objects.get(short_name='ENVISAT')
        self.assertEqual(p.category, 'Earth Observation Satellites')

    def test_get_or_create(self):
        p0 = Platform.objects.get(short_name='ENVISAT')
        p1 = dict(
                Category=p0.category,
                Series_Entity=p0.series_entity,
                Short_Name=p0.short_name,
                Long_Name=p0.long_name)
        p2, cr = Platform.objects.get_or_create(p1)
        self.assertEqual(p0, p2)
        self.assertFalse(cr)


class ProjectTests(BaseForVocabulariesTests):
    def test_get_project(self):
        p = Project.objects.get(short_name='ACSOE')
        self.assertEqual(p.long_name,
            'Atmospheric Chemistry Studies in the Oceanic Environment')


class ScienceKeywordTests(BaseForVocabulariesTests):
    def test_get_science_keyword(self):
        kw = ScienceKeyword.objects.get(variable_level_1='SIGMA NAUGHT')
        self.assertEqual(kw.topic, 'SPECTRAL/ENGINEERING')


class TemporalDataResolutionTests(BaseForVocabulariesTests):
    def test_get_temporal_range(self):
        tr = TemporalDataResolution.objects.get(range='1 minute - < 1 hour')
        self.assertEqual(tr.range, '1 minute - < 1 hour')


class VerticalDataResolutionTests(BaseForVocabulariesTests):
    def test_get_vertical_range(self):
        vr = VerticalDataResolution.objects.get(
                range='10 meters - < 30 meters')
        self.assertEqual(vr.range, '10 meters - < 30 meters')


class CommandsTests(TestCase):

    @patch.object(Parameter.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(DataCenter.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(HorizontalDataResolution.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(ISOTopicCategory.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(Location.objects, 'create_from_vocabularies', autospec=True)
    @patch.object(Platform.objects, 'create_from_vocabularies', autospec=True)
    @patch.object(Project.objects, 'create_from_vocabularies', autospec=True)
    @patch.object(ScienceKeyword.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(TemporalDataResolution.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(VerticalDataResolution.objects, 'create_from_vocabularies',
            autospec=True)
    @patch.object(Instrument.objects, 'create_from_vocabularies',
            autospec=True)
    def test_commands(self, instrument_mock, vdr_mock, tdr_mock, sck_mock,
            project_mock, platform_mock, location_mock, iso_mock, hdr_mock,
            datacenter_mock, parameter_mock):
        call_command('update_vocabularies')
        instrument_mock.assert_called_once_with()
        vdr_mock.assert_called_once_with()
        tdr_mock.assert_called_once_with()
        sck_mock.assert_called_once_with()
        project_mock.assert_called_once_with()
        platform_mock.assert_called_once_with()
        location_mock.assert_called_once_with()
        iso_mock.assert_called_once_with()
        hdr_mock.assert_called_once_with()
        datacenter_mock.assert_called_once_with()
        parameter_mock.assert_called_once_with()


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


class ParameterTests(TestCase):
    ''' This is probably not needed as it should be covered by the
    DatasetParameterTests
    '''
    pass


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


class HorizontalDataResolutionTests(BaseForVocabulariesTests):
    def test_get_horizontal_range(self):
        rr = HorizontalDataResolution.objects.get(range='< 1 meter')
        self.assertEqual(rr.range, '< 1 meter')


class InstrumentTests(BaseForVocabulariesTests):
    def test_get_instrument(self):
        ii = Instrument.objects.get(short_name='ASAR')
        self.assertEqual(ii.long_name, 'Advanced Synthetic Aperature Radar')


class ISOTopicCategoryTests(BaseForVocabulariesTests):
    def test_get_iso_category(self):
        cat = ISOTopicCategory.objects.get(name='Oceans')
        self.assertEqual(cat.name, 'Oceans')


class LocationTests(BaseForVocabulariesTests):
    def test_get_location(self):
        loc = Location.objects.get(subregion2='KENYA')
        self.assertEqual(loc.type, 'AFRICA')


class PlatformTests(BaseForVocabulariesTests):
    def test_get_platform(self):
        p = Platform.objects.get(short_name='ENVISAT')
        self.assertEqual(p.category, 'Earth Observation Satellites')

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


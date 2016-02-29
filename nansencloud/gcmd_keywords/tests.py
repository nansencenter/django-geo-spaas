from django.test import TestCase

from nansencloud.gcmd_keywords.models import DataCenter
from nansencloud.gcmd_keywords.models import HorizontalDataResolution
from nansencloud.gcmd_keywords.models import Instrument
from nansencloud.gcmd_keywords.models import ISOTopicCategory
from nansencloud.gcmd_keywords.models import Location
from nansencloud.gcmd_keywords.models import Platform
from nansencloud.gcmd_keywords.models import Project
from nansencloud.gcmd_keywords.models import ScienceKeyword
from nansencloud.gcmd_keywords.models import TemporalDataResolution
from nansencloud.gcmd_keywords.models import VerticalDataResolution

class DataCenterTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_datacenter(self):
        dc = DataCenter.objects.get(short_name='NERSC')
        # OBS: Note error in the long name - they have been notified and this
        # test should fail at some point...
        self.assertEqual(dc.long_name, 
                'Nansen Environmental and Remote Sensing Centre')

class HorizontalDataResolutionTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_horizontal_range(self):
        rr = HorizontalDataResolution.objects.get(range='< 1 meter')
        self.assertEqual(rr.range, '< 1 meter')

class InstrumentTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_instrument(self):
        ii = Instrument.objects.get(short_name='ASAR')
        self.assertEqual(ii.long_name, 'Advanced Synthetic Aperature Radar')

class ISOTopicCategoryTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_iso_category(self):
        cat = ISOTopicCategory.objects.get(name='Oceans')
        self.assertEqual(cat.name, 'Oceans')

class LocationTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_location(self):
        ADD LOCATIONS TO FIXTURE
        loc = Location.objects.get(subregion2='KENYA')
        self.assertEqual(loc.type, 'AFRICA')

class PlatformTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_platform(self):
        p = Platform.objects.get(short_name='ENVISAT')
        self.assertEqual(p.category, 'Earth Observation Satellites')

class ProjectTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_project(self):
        p = Project.objects.get(short_name='ACSOE')
        self.assertEqual(p.long_name, 
            'Atmospheric Chemistry Studies in the Oceanic Environment')

class ScienceKeywordTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_science_keyword(self):
        kw = ScienceKeyword.objects.get(variable_level_1='SIGMA NAUGHT')
        self.assertEqual(kw.topic, 'SPECTRAL/ENGINEERING')

class TemporalDataResolutionTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_temporal_range(self):
        tr = TemporalDataResolution.objects.get(range='1 minute - < 1 hour')
        self.assertEqual(tr.range, '1 minute - < 1 hour')

class VerticalDataResolutionTests(TestCase):

    fixtures = ["gcmd"]

    def test_get_vertical_range(self):
        vr = VerticalDataResolution.objects.get(
                range='10 meters - < 30 meters')
        self.assertEqual(vr.range, '10 meters - < 30 meters')

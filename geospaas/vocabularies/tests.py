"""Unit tests for the geospaas.vocabularies app"""

import django.db.utils
from django.core.management import call_command
from django.test import TestCase
from mock.mock import MagicMock, patch

from geospaas.vocabularies.models import (DataCenter, HorizontalDataResolution,
                                          Instrument, ISOTopicCategory,
                                          Location, Parameter, Platform,
                                          Project, ScienceKeyword,
                                          TemporalDataResolution,
                                          VerticalDataResolution)


class VocabulariesTestBase(object):
    """Base class for all vocabularies test cases. Contains mocks set up and common tests."""

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

    def _insert_twice(self, attributes):
        """Test that an object of the given model class can't be inserted twice"""
        object1 = self.model(**attributes)
        object2 = self.model(**attributes)

        object1.save()
        object2.save()


class ParameterTests(VocabulariesTestBase, TestCase):
    """Unit tests for the Parameter model"""

    model = Parameter
    model_list = [{
        'standard_name': 'surface_radial_doppler_sea_water_velocity',
        'long_name': 'Radial Doppler Current',
        'short_name': 'Ur',
        'units': 'm s-1',
        'minmax': '-1 1',
        'colormap': 'jet'
    }]
    model.objects.update2 = MagicMock(return_value=None)
    model.objects.get_list2 = MagicMock(return_value=[])

    def test_get_parameter(self):
        """Test retrieval of a Parameter object in the database"""
        parameter = Parameter.objects.get(standard_name=(
            'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'))
        self.assertEqual(parameter.units, 'Hz')

    def test_get_or_create(self):
        """
        The get_or_create() method must not create a new object in the database if one exists with
        the same parameters
        """
        parameter0 = Parameter.objects.get(standard_name=(
            'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'))
        attributes = dict(
            standard_name=parameter0.standard_name,
            short_name=parameter0.short_name,
            units=parameter0.units)
        parameter2, created = Parameter.objects.get_or_create(attributes)
        self.assertEqual(parameter0, parameter2)
        self.assertFalse(created)

    def test_unique_constraint(self):
        """Check that the same Parameter can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'standard_name': 'test', 'short_name': 'test', 'units': 'test',
                'gcmd_science_keyword': ScienceKeyword.objects.latest('id')
            })


class DataCenterTests(VocabulariesTestBase, TestCase):
    """Unit tests for the DataCenter model"""
    model = DataCenter
    model_list = [{
        'Bucket_Level0': 'ACADEMIC',
        'Bucket_Level1': 'OR-STATE/EOARC',
        'Bucket_Level2': '',
        'Bucket_Level3': '',
        'Short_Name': 'OR-STATE/EOARC',
        'Long_Name': 'Eastern Oregon Agriculture Research Center, Oregon State University',
        'Data_Center_URL': 'http://oregonstate.edu/dept/eoarcunion/'
    }]

    def test_get_datacenter(self):
        """Test retrieval of a DataCenter object in the database"""
        data_center = DataCenter.objects.get(short_name='NERSC')
        # OBS: Note error in the long name - they have been notified and this
        # test should fail at some point...
        self.assertEqual(data_center.long_name, 'Nansen Environmental and Remote Sensing Centre')

    def test_get_or_create(self):
        """
        The get_or_create() method must not create a new object in the database if one exists with
        the same parameters
        """
        data_center0 = DataCenter.objects.get(short_name='NERSC')
        attributes = dict(
            Bucket_Level0=data_center0.bucket_level0,
            Bucket_Level1=data_center0.bucket_level1,
            Bucket_Level2=data_center0.bucket_level2,
            Bucket_Level3=data_center0.bucket_level3,
            Short_Name=data_center0.short_name,
            Long_Name=data_center0.long_name,
            Data_Center_URL=data_center0.data_center_url)
        data_center2, created = DataCenter.objects.get_or_create(attributes)
        self.assertEqual(data_center0, data_center2)
        self.assertFalse(created)

    def test_unique_constraint(self):
        """Check that the same DataCenter can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'bucket_level0': 'test',
                'bucket_level1': 'test',
                'bucket_level2': 'test',
                'bucket_level3': 'test',
                'short_name': 'test',
                'long_name': 'test',
                'data_center_url': 'test'
            })


class InstrumentTests(VocabulariesTestBase, TestCase):
    """Unit tests for the Instrument model"""

    model = Instrument
    model_list = [{
        'Category': 'Earth Remote Sensing Instruments',
        'Class': 'Active Remote Sensing',
        'Type': 'Altimeters',
        'Subtype': 'Lidar/Laser Altimeters',
        'Short_Name': 'AIRBORNE LASER SCANNER',
        'Long_Name': ''
    }]

    def test_get_instrument(self):
        """Test retrieval of a Instrument object in the database"""
        instrument = Instrument.objects.get(short_name='ASAR')
        self.assertEqual(instrument.long_name, 'Advanced Synthetic Aperature Radar')

    def test_get_or_create(self):
        """
        The get_or_create() method must not create a new object in the database if one exists with
        the same parameters
        """
        instrument0 = Instrument.objects.get(short_name='ASAR')
        attributes = dict(
            Category=instrument0.category,
            Class=instrument0.instrument_class,
            Type=instrument0.type,
            Subtype=instrument0.subtype,
            Short_Name=instrument0.short_name,
            Long_Name=instrument0.long_name)
        instrument1, created = Instrument.objects.get_or_create(attributes)
        self.assertEqual(instrument0, instrument1)
        self.assertFalse(created)

    def test_unique_constraint(self):
        """Check that the same Instrument can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'category': 'test',
                'instrument_class': 'test',
                'type': 'test',
                'subtype': 'test',
                'short_name': 'test',
                'long_name': 'test'
            })


class ISOTopicCategoryTests(VocabulariesTestBase, TestCase):
    """Unit tests for the ISOTopicCategory model"""

    model = ISOTopicCategory
    model_list = [{'iso_topic_category': 'Biota'}]

    def test_get_iso_category(self):
        """Test retrieval of a ISOTopicCategory object in the database"""
        cat = ISOTopicCategory.objects.get(name='Oceans')
        self.assertEqual(cat.name, 'Oceans')

    def test_get_or_create(self):
        """
        The get_or_create() method must not create a new object in the database if one exists with
        the same parameters
        """
        iso_topic_category0 = ISOTopicCategory.objects.get(name='Oceans')
        attributes = dict(iso_topic_category=iso_topic_category0.name)
        iso_topic_category2, created = ISOTopicCategory.objects.get_or_create(attributes)
        self.assertEqual(iso_topic_category0, iso_topic_category2)
        self.assertFalse(created)

    def test_unique_constraint(self):
        """Check that the same ISOTopicCategory can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({'name': 'test'})


class LocationTests(VocabulariesTestBase, TestCase):
    """Unit tests for the Location model"""

    model = Location
    model_list = [{
        'Location_Category': 'CONTINENT',
        'Location_Type': 'AFRICA',
        'Location_Subregion1':
        'CENTRAL AFRICA',
        'Location_Subregion2':
        'ANGOLA',
        'Location_Subregion3': ''
    }]

    def test_get_location(self):
        """Test retrieval of a Location object in the database"""
        location = Location.objects.get(subregion2='KENYA')
        self.assertEqual(location.type, 'AFRICA')

    def test_get_or_create(self):
        """
        The get_or_create() method must not create a new object in the database if one exists with
        the same parameters
        """
        location0 = Location.objects.get(subregion2='KENYA')
        attributes = dict(
            Location_Category=location0.category,
            Location_Type=location0.type,
            Location_Subregion1=location0.subregion1,
            Location_Subregion2=location0.subregion2,
            Location_Subregion3=location0.subregion3)
        location2, created = Location.objects.get_or_create(attributes)
        self.assertEqual(location0, location2)
        self.assertFalse(created)

    def test_unique_constraint(self):
        """Check that the same Location can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'category': 'test',
                'type': 'test',
                'subregion1': 'test',
                'subregion2': 'test',
                'subregion3': 'test'
            })


class PlatformTests(VocabulariesTestBase, TestCase):
    """Unit tests for the Platform model"""

    model = Platform
    model_list = [{
        'Category': 'Aircraft',
        'Series_Entity': '',
        'Short_Name': 'A340-600',
        'Long_Name': 'Airbus A340-600'
    }]

    def test_get_platform(self):
        """Test retrieval of a Platform object in the database"""
        platform = self.model.objects.get(short_name='ENVISAT')
        self.assertEqual(platform.category, 'Earth Observation Satellites')

    def test_get_or_create(self):
        """
        The get_or_create() method must not create a new object in the database if one exists with
        the same parameters
        """
        platform0 = self.model.objects.get(short_name='ENVISAT')
        attributes = dict(
            Category=platform0.category,
            Series_Entity=platform0.series_entity,
            Short_Name=platform0.short_name,
            Long_Name=platform0.long_name)
        platform2, created = Platform.objects.get_or_create(attributes)
        self.assertEqual(platform0, platform2)
        self.assertFalse(created)

    def test_unique_constraint(self):
        """Check that the same Platform can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'category': 'test',
                'series_entity': 'test',
                'short_name': 'test',
                'long_name': 'test'
            })


class ProjectTests(VocabulariesTestBase, TestCase):
    """Unit tests for the Project model"""

    model = Project
    model_list = [{
        'Bucket': 'A - C',
        'Short_Name': 'AAE',
        'Long_Name': 'Australasian Antarctic Expedition of 1911-14'
    }]

    def test_get_project(self):
        """Test retrieval of a Project object in the database"""
        project = self.model.objects.get(short_name='ACSOE')
        self.assertEqual(project.long_name,
                         'Atmospheric Chemistry Studies in the Oceanic Environment')

    def test_unique_constraint(self):
        """Check that the same Project can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'bucket': 'test',
                'short_name': 'test',
                'long_name': 'test'
            })


class ScienceKeywordTests(VocabulariesTestBase, TestCase):
    """Unit tests for the ScienceKeyword model"""

    model = ScienceKeyword
    model_list = [{
        'Category': 'EARTH SCIENCE SERVICES',
        'Topic': 'DATA ANALYSIS AND VISUALIZATION',
        'Term': 'CALIBRATION/VALIDATION',
        'Variable_Level_1': 'CALIBRATION',
        'Variable_Level_2': '',
        'Variable_Level_3': '',
        'Detailed_Variable': ''
    }]

    def test_get_science_keyword(self):
        """Test retrieval of a ScienceKeyword object in the database"""
        keyword = self.model.objects.get(variable_level_1='SIGMA NAUGHT')
        self.assertEqual(keyword.topic, 'SPECTRAL/ENGINEERING')

    def test_unique_constraint(self):
        """Check that the same ScienceKeyword can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'category': 'test',
                'topic': 'test',
                'term': 'test',
                'variable_level_1': 'test',
                'variable_level_2': 'test',
                'variable_level_3': 'test',
                'detailed_variable': 'test'
            })


class TemporalDataResolutionTests(VocabulariesTestBase, TestCase):
    """Unit tests for the TemporalDataResolution model"""

    model = TemporalDataResolution
    model_list = [{'Temporal_Resolution_Range': '1 minute - < 1 hour'}]

    def test_get_temporal_range(self):
        """Test retrieval of a TemporalDataResolution object in the database"""
        temporal_resolution = self.model.objects.get(range='1 minute - < 1 hour')
        self.assertEqual(temporal_resolution.range, '1 minute - < 1 hour')

    def test_unique_constraint(self):
        """Check that the same TemporalDataResolution can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({'range': 'test'})


class HorizontalDataResolutionTests(VocabulariesTestBase, TestCase):
    """Unit tests for the HorizontalDataResolution model"""

    model = HorizontalDataResolution
    model_list = [{
        'Horizontal_Resolution_Range': '1 km - < 10 km or approximately .01 degree - < .09 degree'
    }]

    def test_get_horizontal_range(self):
        """Test retrieval of a HorizontalDataResolution object in the database"""
        horizontal_resolution = self.model.objects.get(range='< 1 meter')
        self.assertEqual(horizontal_resolution.range, '< 1 meter')

    def test_unique_constraint(self):
        """Check that the same HorizontalDataResolution can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({'range': 'test'})


class VerticalDataResolutionTests(VocabulariesTestBase, TestCase):
    """Unit tests for the VerticalDataResolution model"""

    model = VerticalDataResolution
    model_list = [{'Vertical_Resolution_Range': '1 meter - < 10 meters'}]

    def test_get_vertical_range(self):
        """Test retrieval of a VerticalDataResolution object in the database"""
        vertical_resolution = self.model.objects.get(range='10 meters - < 30 meters')
        self.assertEqual(vertical_resolution.range, '10 meters - < 30 meters')

    def test_unique_constraint(self):
        """Check that the same VerticalDataResolution can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({'range': 'test'})


class CommandsTests(TestCase):
    """Unit tests for the custom commands of the vocabularies app"""

    def setUp(self):
        return_value = [{'Revision': '2019-02-13 08:48:55'}]
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
        """Check that the command does not update the vocabularies if they are present"""

        call_command('update_vocabularies')
        # check that get_list was called only once
        for mock in self.get_list_mocks:
            mock.assert_called()
        # check that update was never called
        for mock in self.update_mocks:
            mock.assert_not_called()

    def test_command_update_vocabularies_force(self):
        """
        Check that the command updates the vocabularies even if they are present when --force is
        specified
        """

        call_command('update_vocabularies', '--force')
        # check that get_list was called only once
        for mock in self.get_list_mocks:
            mock.assert_called()
        # check that update was called
        for mock in self.update_mocks:
            mock.assert_called()

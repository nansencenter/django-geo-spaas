"""Tests for the utils module"""
import re
import unittest
import unittest.mock as mock
from datetime import datetime

import django.test
import shapely.geometry
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc

import geospaas.harvesting.normalizers.errors as errors
import geospaas.harvesting.normalizers.utils as utils
from geospaas.vocabularies.models import Keyword, Parameter


class TimeTestCase(unittest.TestCase):
    """Tests for utilities dealing with time"""

    def test_create_datetime_year_month_day(self):
        """test create_datetime with a year, month and day"""
        self.assertEqual(
            utils.create_datetime(2020, 10, 15),
            datetime(2020, 10, 15).replace(tzinfo=tzutc())
        )

    def test_create_datetime_year_day_of_year(self):
        """test create_datetime with a year and day of year"""
        self.assertEqual(
            utils.create_datetime(2020, day_of_year=35),
            datetime(2020, 2, 4).replace(tzinfo=tzutc())
        )

    def test_create_datetime_year_month_day_time(self):
        """test create_datetime with a year, month, day and time"""
        self.assertEqual(
            utils.create_datetime(2020, 10, 15, hour=10, minute=25, second=38),
            datetime(2020, 10, 15, 10, 25, 38).replace(tzinfo=tzutc())
        )

    def test_create_datetime_year_day_of_year_time(self):
        """test create_datetime with a year, day of year and time"""
        self.assertEqual(
            utils.create_datetime(2020, day_of_year=35, hour=23, minute=1, second=40),
            datetime(2020, 2, 4, 23, 1, 40).replace(tzinfo=tzutc())
        )

    def test_yearmonth_regex(self):
        """The YEARMONTH_REGEX should provide a 'year' and 'month'
        named groups
        """
        self.assertDictEqual(
            re.match(utils.YEARMONTH_REGEX, '202010').groupdict(),
            {'year': '2020', 'month': '10'}
        )

    def test_yearmonthday_regex(self):
        """The YEARMONTHDAY_REGEX should provide a 'year', 'month'
        and 'day' named groups
        """
        self.assertDictEqual(
            re.match(utils.YEARMONTHDAY_REGEX, '20201017').groupdict(),
            {'year': '2020', 'month': '10', 'day': '17'}
        )

    def test_find_time_coverage(self):
        """find_time_coverage() should extract the time coverage from a
        URL using the given regexes and functions
        """
        time_patterns = (
            (
                re.compile(rf"dataset_{utils.YEARMONTHDAY_REGEX}.nc$"),
                utils.create_datetime,
                lambda time: (time, time + relativedelta(days=1))
            ),
            (
                re.compile(rf"dataset_{utils.YEARMONTH_REGEX}.nc$"),
                utils.create_datetime,
                lambda time: (time, time + relativedelta(months=1))
            )
        )
        self.assertTupleEqual(
            utils.find_time_coverage(time_patterns, 'ftp://foo/dataset_20200205.nc'),
            (datetime(2020, 2, 5, tzinfo=tzutc()), datetime(2020, 2, 6, tzinfo=tzutc())))
        self.assertTupleEqual(
            utils.find_time_coverage(time_patterns, 'ftp://foo/dataset_202002.nc'),
            (datetime(2020, 2, 1, tzinfo=tzutc()), datetime(2020, 3, 1, tzinfo=tzutc())))

    def test_find_time_coverage_not_found(self):
        """A MetadataNormalizationError must be raised when no time
        coverage can be extracted
        """
        time_patterns = ((re.compile(r'foo'), None, None),)
        with self.assertRaises(errors.MetadataNormalizationError):
            utils.find_time_coverage(time_patterns, 'bar')


class UtilsTestCase(django.test.TestCase):
    """Test case for utils functions"""
    fixtures = ['harvesting_vocabularies.json']

    def test_dict_to_string(self):
        """dict_to_string() should return the proper representation"""
        self.assertEqual(
            utils.dict_to_string({'key1': 'value1', 'key2': 'value2'}),
            'key1: value1;key2: value2'
        )

    def test_empty_dict_to_string(self):
        """The representation of an empty dict is an empty string"""
        self.assertEqual(utils.dict_to_string({}), '')

    def test_translate_pythesint_keyword(self):
        """Should return the right keyword given an alias"""
        translation_dict = {
            'keyword1': ('alias11', 'alias12'),
            'keyword2': ('alias21', 'alias22'),
        }
        self.assertEqual(utils.translate_pythesint_keyword(translation_dict, 'alias11'), 'keyword1')
        self.assertEqual(utils.translate_pythesint_keyword(translation_dict, 'alias22'), 'keyword2')
        self.assertEqual(utils.translate_pythesint_keyword(translation_dict, 'alias3'), 'alias3')

    def test_raises_decorator(self):
        """Test that the `raises()` decorator raises a
        MetadataNormalizationError when the function it decorates
        raises the exception given as argument to the decorator
        """
        # the type annotation prevents Pylance from wrongfully marking
        # the following code as unreachable
        @utils.raises(KeyError)
        def get_foo(self, dataset_info) -> None:
            raise KeyError

        with self.assertRaises(errors.MetadataNormalizationError) as raised:
            get_foo(mock.Mock(), mock.Mock())
        self.assertIsInstance(raised.exception.__cause__, KeyError)

    def test_raises_decorator_with_tuple(self):
        """Test that the `raises()` decorator raises a
        MetadataNormalizationError when the function it decorates
        raises one of the exceptions given as argument to the decorator
        """
        # the type annotation prevents Pylance from wrongfully marking
        # the following code as unreachable
        @utils.raises((KeyError, IndexError))
        def get_foo(self, dataset_info) -> None:
            raise IndexError

        with self.assertRaises(errors.MetadataNormalizationError) as raised:
            get_foo(mock.Mock(), mock.Mock())
        self.assertIsInstance(raised.exception.__cause__, IndexError)

    def test_raises_decorator_wrong_exception(self):
        """Test that the `raises()` decorator does not catch exceptions
        which are not in its arguments
        """
        # the type annotation prevents Pylance from wrongfully marking
        # the following code as unreachable
        @utils.raises(KeyError)
        def get_foo(self, dataset_info) -> None:
            raise ValueError

        with self.assertRaises(ValueError):
            get_foo(mock.Mock(), mock.Mock())

    def test_wkt_polygon_from_wgs84_limits(self):
        """Test making a WKT polygon string from box bounds"""
        self.assertEqual(
            utils.wkt_polygon_from_wgs84_limits(90, 60, 180, -180),
            'POLYGON((-180 60,180 60,180 90,-180 90,-180 60))')

    def test_translate_west_coordinates(self):
        """Test translating west coordinates from [-180, 0[ to
        [180, 360[
        """
        self.assertEqual(
            utils.translate_west_coordinates(
                shapely.geometry.MultiPolygon([(
                    [(10, 80), (-10, 90), (-180, 80), (10, 80)],
                    [((-20, 83), (-20, 82), (-40, 81), (-20, 83))]
                )])),
            shapely.geometry.MultiPolygon([(
                [(10, 80), (350, 90), (180, 80), (10, 80)],
                [((340, 83), (340, 82), (320, 81), (340, 83))]
            )])
        )

    def test_restore_west_coordinates_east_idl(self):
        """Test translating west coordinates back to [-180, 0[ for a
        polygon on the east side of the IDL
        """
        self.assertEqual(
            utils.restore_west_coordinates(
                shapely.geometry.MultiPolygon([(
                    [(180, 80), (350, 80), (350, 90), (180, 80)],
                    [((340, 83), (340, 82), (320, 81), (340, 83))]
                )])),
            shapely.geometry.MultiPolygon([(
                [(-180, 80), (-10, 80), (-10, 90), (-180, 80)],
                [((-20, 83), (-20, 82), (-40, 81), (-20, 83))]
            )])
        )

    def test_restore_west_coordinates_west_idl(self):
        """Test translating west coordinates back to [-180, 0[ for a
        polygon on the west side of the IDL. No modification should be
        made
        """
        self.assertEqual(
            utils.restore_west_coordinates(
                shapely.geometry.MultiPolygon([
                    ([(10, 80), (10, 90), (20, 80), (10, 80)], [])
                ])),
            shapely.geometry.MultiPolygon([
                ([(10, 80), (10, 90), (20, 80), (10, 80)], [])
            ])
        )

    def test_split_multipolygon_along_idl(self):
        """Test splitting a multipolygon along the IDL"""
        self.assertEqual(
            utils.split_multipolygon_along_idl(
                shapely.geometry.MultiPolygon([
                    ([(-170, 80), (-170, 90), (170, 90), (170, 80), (-170, 80)], [])
                ])),
            shapely.geometry.MultiPolygon([
                ([(-180, 90), (-170, 90), (-170, 80), (-180, 80), (-180, 90)], []),
                ([(180, 80), (170, 80), (170, 90), (180, 90), (180, 80)], []),
            ])
        )

    def test_split_multipolygon_along_idl_global_coverage(self):
        """When a dataset has global coverage, not splitting is needed"""
        multipolygon = shapely.geometry.MultiPolygon([
            ([(-180, 90), (-180, -90), (180, -90), (180, 90), (-180, 90)], [])
        ])
        self.assertEqual(
            utils.split_multipolygon_along_idl(multipolygon),
            multipolygon)

    def test_create_parameter_list(self):
        """Test creating parameters from a list of names"""
        expected_parameters = [
            Parameter.objects.get(id=1),
            Parameter.objects.get(id=3)
        ]
        self.assertListEqual(utils.create_parameter_list(('foo', 'bar')), expected_parameters)

    def test_create_parameter_list_not_found(self):
        """Return empty list when nothing is found"""
        self.assertListEqual(utils.create_parameter_list(('idontexist',)), [])

    def test_find_keywords(self):
        """Test finding keywords"""
        self.assertListEqual(
            utils.find_keywords([{'data__icontains': 'foo'}]),
            [Keyword.objects.get(id=1)])
        self.assertListEqual(utils.find_keywords([{'data__icontains': 'baz'}]), [])

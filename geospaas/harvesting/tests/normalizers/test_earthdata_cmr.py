"""Tests for the ACDD metadata normalizer"""
import unittest
import unittest.mock as mock
from datetime import datetime

from dateutil.tz import tzutc

import geospaas.harvesting.normalizers as normalizers
from geospaas.harvesting.crawlers.base import DatasetInfo
from geospaas.harvesting.normalizers.errors import MetadataNormalizationError


class EarthdataCMRMetadataNormalizerTestCase(unittest.TestCase):
    """Tests for the Creodias API attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.earthdata_cmr.EarthdataCMRMetadataNormalizer()

    def test_entry_id(self):
        """Test getting the ID"""
        dataset_info = DatasetInfo('', {
            'umm': {
                "DataGranule": {
                    "Identifiers": [
                        {
                            "IdentifierType": "ProducerGranuleId",
                            "Identifier": "V2020245000600.L2_SNPP_OC.nc"
                        }
                    ]
                }
            }
        })
        self.assertEqual(self.normalizer.get_entry_id(dataset_info), 'V2020245000600.L2_SNPP_OC')

    def test_entry_id_from_granuleUR(self):
        """Test getting the ID from the GranuleUR field"""
        self.assertEqual(
            self.normalizer.get_entry_id(DatasetInfo('', {'umm': {'GranuleUR': 'foo'}})),
            'foo')

    def test_entry_id_missing_attribute(self):
        """A MetadataNormalizationError must be raised if the raw
        attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_id(DatasetInfo('', {'umm': {'foo': 'bar'}}))

    def test_entry_title(self):
        """Test getting the title"""
        dataset_info = DatasetInfo('', {
            'umm': {
                "DataGranule": {
                    "Identifiers": [
                        {
                            "IdentifierType": "ProducerGranuleId",
                            "Identifier": "V2020245000600.L2_SNPP_OC.nc"
                        }
                    ]
                }
            }
        })
        self.assertEqual(self.normalizer.get_entry_title(dataset_info), 'V2020245000600.L2_SNPP_OC')

    def test_entry_title_missing_attribute(self):
        """A MetadataNormalizationError must be raised if the raw
        attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_entry_title(DatasetInfo('', {'umm': {'foo': 'bar'}}))

    def test_summary(self):
        """Test getting the summary"""
        dataset_info = DatasetInfo('', {
            "umm": {
                "TemporalExtent": {
                    "RangeDateTime": {
                        "BeginningDateTime": "2020-09-01T00:06:00Z",
                        "EndingDateTime": "2020-09-01T00:11:59Z"
                    }
                },
                "Platforms": [
                    {
                        "ShortName": "SUOMI-NPP",
                        "Instruments": [
                            {
                                "ShortName": "VIIRS"
                            }
                        ]
                    }
                ],
                "CollectionReference": {
                    "ShortName": "VIIRSN_L2_OC",
                    "Version": "2018"
                }
            }
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            'Description: Platform=SUOMI-NPP, ' +
            'Instrument=VIIRS, Start date=2020-09-01T00:06:00Z;' +
            'Processing level: 2')
        dataset_info.metadata['umm']['CollectionReference']['ShortName'] = 'VIIRSN'
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            'Description: Platform=SUOMI-NPP, ' +
            'Instrument=VIIRS, Start date=2020-09-01T00:06:00Z')

    def test_summary_no_platform(self):
        """Test getting a summary when no platform info is available
        """
        dataset_info = DatasetInfo('', {
            "umm": {
                "TemporalExtent": {
                    "RangeDateTime": {
                        "BeginningDateTime": "2020-09-01T00:06:00Z",
                        "EndingDateTime": "2020-09-01T00:11:59Z"
                    }
                },
                "CollectionReference": {
                    "ShortName": "VIIRSN_L2_OC",
                    "Version": "2018"
                }
            }
        })
        self.assertEqual(
            self.normalizer.get_summary(dataset_info),
            'Description: Start date=2020-09-01T00:06:00Z;Processing level: 2')

    def test_summary_missing_attribute(self):
        """A MetadataNormalizationError must be raised if the raw
        attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_summary(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_summary(DatasetInfo('', {"umm": {'foo': 'bar'}}))

    def test_time_coverage_start(self):
        """Test getting the start of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_start(DatasetInfo('', {
                "umm": {
                    "TemporalExtent": {
                        "RangeDateTime": {
                            "BeginningDateTime": "2020-09-01T00:06:00Z",
                            "EndingDateTime": "2020-09-01T00:11:59Z"
                        }
                    }
                }
            })),
            datetime(year=2020, month=9, day=1, hour=0, minute=6, second=0, tzinfo=tzutc()))

    def test_time_coverage_start_missing_attribute(self):
        """A MetadataNormalizationError must be raised if the raw
        attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_start(DatasetInfo('', {"umm": {'foo': 'bar'}}))

    def test_time_coverage_end(self):
        """Test getting the end of the time coverage"""
        self.assertEqual(
            self.normalizer.get_time_coverage_end(DatasetInfo('', {
                "umm": {
                    "TemporalExtent": {
                        "RangeDateTime": {
                            "BeginningDateTime": "2020-09-01T00:06:00Z",
                            "EndingDateTime": "2020-09-01T00:11:59Z"
                        }
                    }
                }
            })),
            datetime(year=2020, month=9, day=1, hour=0, minute=11, second=59, tzinfo=tzutc()))

    def test_time_coverage_end_missing_attribute(self):
        """A MetadataNormalizationError must be raised if the raw
        attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_time_coverage_end(DatasetInfo('', {'umm': {'foo': 'bar'}}))

    def test_get_keywords(self):
        """Test getting the keywords"""
        dataset_info = DatasetInfo('', {
            "meta": {"provider-id": "OB_DAAC"},
            "umm": {
                "Platforms": [
                    {
                        "ShortName": "SUOMI-NPP",
                        "Instruments": [
                            {
                                "ShortName": "VIIRS"
                            }
                        ]
                    }
                ],
            }
        })
        with mock.patch('geospaas.harvesting.normalizers.utils.find_keywords'
                        ) as mock_find_keywords:
            self.normalizer.get_keywords(dataset_info)
            mock_find_keywords.assert_called_once_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'SUOMI-NPP'},
                {'kind': 'gcmd_instrument', 'data__icontains': 'VIIRS'},
                {'kind': 'gcmd_provider', 'data__icontains': 'OB_DAAC'},
            ])

    def test_get_keywords_no_info(self):
        """Test getting the keywords when information is missing"""
        dataset_info = DatasetInfo('', {
            "meta": {"provider-id": "OB_DAAC"},
            "umm": {"Platforms": [{"ShortName": "SUOMI-NPP",}],}
        })
        with mock.patch('geospaas.harvesting.normalizers.utils.find_keywords'
                        ) as mock_find_keywords:
            self.normalizer.get_keywords(dataset_info)
            mock_find_keywords.assert_called_once_with([
                {'kind': 'gcmd_platform', 'data__icontains': 'SUOMI-NPP'},
                {'kind': 'gcmd_provider', 'data__icontains': 'OB_DAAC'},
            ])

    def test_location_geometry_one_bounding_box(self):
        """Test getting the location_geometry from one bounding box"""

        dataset_info = DatasetInfo('', {
            'umm': {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "Geometry": {
                            "BoundingRectangles": [
                                {
                                    "EastBoundingCoordinate": -84.524773,
                                    "SouthBoundingCoordinate": -84.093506,
                                    "NorthBoundingCoordinate": -54.569214,
                                    "WestBoundingCoordinate": 155.812729
                                }
                            ]
                        }
                    }
                }
            }
        })
        expected_wkt = ('GEOMETRYCOLLECTION('
            'POLYGON(('
            '155.812729 -84.093506,'
            '-84.524773 -84.093506,'
            '-84.524773 -54.569214,'
            '155.812729 -54.569214,'
            '155.812729 -84.093506)))')
        self.assertEqual(self.normalizer.get_location_geometry(dataset_info), expected_wkt)

    def test_location_geometry_multiple_bounding_boxes(self):
        """Test getting the location_geometry from multiple bounding boxes"""

        dataset_info = DatasetInfo('', {
            'umm': {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "Geometry": {
                            "BoundingRectangles": [
                                {
                                    "EastBoundingCoordinate": -84.524773,
                                    "SouthBoundingCoordinate": -84.093506,
                                    "NorthBoundingCoordinate": -54.569214,
                                    "WestBoundingCoordinate": 155.812729
                                },
                                {
                                    "EastBoundingCoordinate": 80.0,
                                    "SouthBoundingCoordinate": 50.0,
                                    "NorthBoundingCoordinate": 60.0,
                                    "WestBoundingCoordinate": 70.0
                                }
                            ]
                        }
                    }
                }
            }
        })
        expected_wkt = ('GEOMETRYCOLLECTION('
            'POLYGON(('
            '155.812729 -84.093506,'
            '-84.524773 -84.093506,'
            '-84.524773 -54.569214,'
            '155.812729 -54.569214,'
            '155.812729 -84.093506)),'
            'POLYGON(('
            '70.0 50.0,'
            '80.0 50.0,'
            '80.0 60.0,'
            '70.0 60.0,'
            '70.0 50.0)))')
        self.assertEqual(self.normalizer.get_location_geometry(dataset_info), expected_wkt)

    def test_location_geometry_gpolygons(self):
        """Test getting the location_geometry from gpolygons"""

        dataset_info = DatasetInfo('', {
            'umm': {
                "SpatialExtent": {
                    "HorizontalSpatialDomain": {
                        "Geometry": {
                            "GPolygons": [
                                {
                                    'Boundary': {
                                        'Points': [
                                            {'Longitude': 80.0, 'Latitude': 50.0},
                                            {'Longitude': 60.0, 'Latitude': 50.0},
                                            {'Longitude': 60.0, 'Latitude': 70.0},
                                            {'Longitude': 80.0, 'Latitude': 70.0},
                                            {'Longitude': 80.0, 'Latitude': 50.0},
                                        ]
                                    },
                                    'ExclusiveZone': {
                                        'Boundaries': [{
                                            'Points': [
                                                {'Longitude': 75, 'Latitude': 55},
                                                {'Longitude': 65, 'Latitude': 55},
                                                {'Longitude': 65, 'Latitude': 65},
                                                {'Longitude': 75, 'Latitude': 65},
                                                {'Longitude': 75, 'Latitude': 55},
                                            ]
                                        }]
                                    }
                                },
                                {
                                    'Boundary': {
                                        'Points': [
                                            {'Longitude': 20.0, 'Latitude': 40.0},
                                            {'Longitude': 20.0, 'Latitude': 30.0},
                                            {'Longitude': 10.0, 'Latitude': 30.0},
                                            {'Longitude': 20.0, 'Latitude': 40.0},
                                        ]
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        })
        expected_wkt = (
            'GEOMETRYCOLLECTION('
            'POLYGON ((80 50, 60 50, 60 70, 80 70, 80 50), (75 55, 65 55, 65 65, 75 65, 75 55)),'
            'POLYGON ((20 40, 20 30, 10 30, 20 40)))')
        self.assertEqual(self.normalizer.get_location_geometry(dataset_info), expected_wkt)

    def test_location_geometry_missing_attribute(self):
        """A MetadataNormalizationError must be raised if the raw
        attribute is missing
        """
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(DatasetInfo(''))
        with self.assertRaises(MetadataNormalizationError):
            self.normalizer.get_location_geometry(DatasetInfo('', {'umm': {'foo': 'bar'}}))

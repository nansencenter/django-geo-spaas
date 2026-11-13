"""Tests for the ops module"""

import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import nco
import netCDF4
import numpy as np
from osgeo import gdal, osr

import geospaas.processing.ops as ops


class CroppingTestCase(unittest.TestCase):
    """Tests for ops functions"""

    @staticmethod
    def create_netcdf_dataset(path):
        """Create a test netCDF file covering the following box:
        south-west corner: 0,0; upper-north corner: 10,10
        """
        dataset = netCDF4.Dataset(str(path), 'w', format='NETCDF4')
        dataset.createDimension('longitude', 10)
        dataset.createDimension('latitude', 10)
        longitudes = dataset.createVariable('longitude', 'i1', ('longitude'))
        latitudes = dataset.createVariable('latitude', 'i1', ('latitude',))
        data = dataset.createVariable('data', 'i1', ('longitude', 'latitude'))
        data2 = dataset.createVariable('data2', 'i1', ('longitude', 'latitude'))
        longitudes[:] = range(10)
        latitudes[:] = range(10)
        data[:] = np.zeros((10, 10))
        data2[:] = np.ones((10, 10))
        dataset.close()

    @staticmethod
    def create_geotiff_dataset(path):
        """Create a test GeoTIFF file covering the following box:
        south-west corner: 0,0; upper-north corner: 10,10
        """
        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(str(path), 10, 10, 2, gdal.GDT_Byte)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        dataset.SetProjection(srs.ExportToWkt())
        dataset.SetGeoTransform([0, 1, 0, 10, 0, -1])
        band1 = dataset.GetRasterBand(1)
        band1.WriteArray(np.zeros((10, 10)))
        band2 = dataset.GetRasterBand(2)
        band2.WriteArray(np.ones((10, 10)))
        dataset = None

    def test_gdal_crop(self):
        """Test cropping a GeoTIFF file using GDAL"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_file = Path(tmp_dir, 'dataset.tiff')
            cropped_file = Path(tmp_dir, 'cropped.tiff')
            self.create_geotiff_dataset(original_file)

            ops.gdal_crop(original_file, cropped_file, [0, 5, 5, 0])

            dataset = gdal.Open(str(cropped_file))

            ulx, dx, _, uly, _, dy = dataset.GetGeoTransform()
            # upper left corner
            self.assertEqual(ulx, 0)
            self.assertEqual(uly, 5)
            # lower right corner
            self.assertEqual(ulx + dataset.RasterXSize * dx, 5)
            self.assertEqual(uly + dataset.RasterYSize * dy, 0)

    def test_netcdf_crop(self):
        """Test cropping a netCDF file"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_file = Path(tmp_dir, 'dataset.nc')
            cropped_file = Path(tmp_dir, 'cropped.nc')
            self.create_netcdf_dataset(original_file)

            ops.nco_crop(original_file, cropped_file, [0, 5, 5, 0])

            dataset = netCDF4.Dataset(str(cropped_file))
            self.assertListEqual(list(dataset.variables['longitude'][:]), list(range(6)))
            self.assertListEqual(list(dataset.variables['latitude'][:]), list(range(6)))
            self.assertEqual(dataset.variables['data'].shape, (6, 6))
            self.assertEqual(dataset.variables['data2'].shape, (6, 6))

    def test_netcdf_crop_error(self):
        """Test handling error during netCDF cropping"""
        with mock.patch('geospaas.processing.ops.nco.ncks',
                        side_effect=nco.NCOException('', '', 1)), \
             mock.patch('geospaas.processing.ops.find_netcdf_lon_lat',
                        return_value=('lon', 'lat')):
            with self.assertRaises(RuntimeError):
                ops.nco_crop('', '', [1, 2, 3, 4])

    def test_nco_unavailable(self):
        """An error must be raised if nco is not installed"""
        with mock.patch('geospaas.processing.ops.nco', None), \
             mock.patch('geospaas.processing.ops.find_netcdf_lon_lat',
                        return_value=('lon', 'lat')):
            with self.assertRaises(RuntimeError):
                ops.nco_crop('', '', [1, 2, 3, 4])

    def test_find_netcdf_lon_lat(self):
        """Test find the longitude and latitude variable names in a
        netCDF file
        """
        mock_dataset = mock.Mock()
        with mock.patch('netCDF4.Dataset', return_value=mock_dataset):
            mock_dataset.dimensions = ('longitude', 'latitude')
            self.assertTupleEqual(ops.find_netcdf_lon_lat(''), ('longitude', 'latitude'))

            mock_dataset.dimensions = ('TIME', 'LONGITUDE', 'LATITUDE')
            self.assertTupleEqual(ops.find_netcdf_lon_lat(''), ('LONGITUDE', 'LATITUDE'))

            mock_dataset.dimensions = ('lon', 'lat')
            self.assertTupleEqual(ops.find_netcdf_lon_lat(''), ('lon', 'lat'))

            mock_dataset.dimensions = ('foo', 'bar')
            with self.assertRaises(RuntimeError):
                ops.find_netcdf_lon_lat('')

    def test_crop(self):
        """Test that the right cropping function is called"""
        with mock.patch('geospaas.processing.ops.gdal_crop') as mock_gdal_crop, \
             mock.patch('geospaas.processing.ops.nco_crop') as mock_nco_crop:
            ops.crop(Path('dataset.tiff'), '', [1, 2, 3, 4])
            mock_gdal_crop.assert_called_once()
            ops.crop(Path('dataset.nc'), '', [1, 2, 3, 4])
            mock_nco_crop.assert_called_once()

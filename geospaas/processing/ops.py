"""Functions for various operations on dataset files (cropping,
reprojection, etc.)
"""
import logging
from enum import Enum

import netCDF4
try:
    from nco import Nco, NCOException
    nco = Nco()
except (ImportError, TypeError):  # pragma: no cover
    nco = None

try:
    from osgeo import gdal
except ImportError:  # pragma: no cover
    import gdal


logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """Output formats supported by GDAL"""
    geotiff = 'GTiff'
    netcdf = 'netCDF'
    vrt = 'VRT'


def gdal_crop(in_file, out_file, bbox, output_format=OutputFormat.geotiff):
    """Cropping function using GDAL translate.
    Works for GeoTIFF, for example.
    """
    options = gdal.TranslateOptions(
        projWin=tuple(str(b) for b in bbox[0:4]),
        format=output_format.value)
    gdal.Translate(str(out_file), str(in_file), options=options)


def find_netcdf_lon_lat(in_file):
    """Try to find the dimension names for longitude and latitude in a
    netCDF file
    """
    dataset = netCDF4.Dataset(in_file)
    longitude_name = ''
    latitude_name = ''

    for dimension in dataset.dimensions:
        lowercase_dimension = dimension.lower()
        if 'lon' in lowercase_dimension:
            longitude_name = dimension
        if 'lat' in lowercase_dimension:
            latitude_name = dimension

    if longitude_name and latitude_name:
        return (longitude_name, latitude_name)
    else:
        raise RuntimeError(
            f"Could not determine longitude and latitude dimensions names for {in_file}")


def nco_crop(in_file, out_file, bbox):
    """Cropping function for netCDF files. Uses NCO.
    """
    longitude_name, latitude_name = find_netcdf_lon_lat(in_file)
    try:
        nco.ncks(
            input=str(in_file),
            output=str(out_file),
            options=[
                f"-d {latitude_name},{bbox[3]:f},{bbox[1]:f}",
                f"-d {longitude_name},{bbox[0]:f},{bbox[2]:f}",
            ])
    except NCOException as error:
        raise RuntimeError('An error happened during cropping. Please check that the bounding '
                           'box is within the datasets spatial coverage') from error
    except AttributeError:
        raise RuntimeError('nco is not available')


def crop(in_file, out_file, bbox):
    """Subset a dataset file using a bounding box.
    bbox is a sequence containing the limits of the bounding box in the
    projection of the dataset in the following order:
    west, north, east, south
    """
    in_file = str(in_file)
    if in_file.endswith('.nc'):
        nco_crop(in_file, out_file, bbox)
    else:  # untested
        gdal_crop(in_file, out_file, bbox)

import os
import glob
from datetime import datetime as dt

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, Polygon, GEOSException
from django.contrib.gis.gdal import GDALException

from geospaas.catalog.models import Dataset

def valid_date(s):
    ''' Test input datestring '''
    try:
        return dt.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise TypeError(msg)


class ProcessingBaseCommand(BaseCommand):
    """ Base class for geospaas-based processing commands for initial filtering on space and time.

    Usage
    -----
    from geospaas.utils import ProcessingBaseCommand
    class SomeProcessingCommand(ProcessingBaseCommand):
        args = '<filename filename ...>'
        help = 'Run classification of texture features'

        def handle(self, *args, **options):
            # find input datasets
            inp_datasets = self.find_datasets(**options)

            # continue to filter inp_datasets
            # continue to process inp_datasets
    """
    def add_arguments(self, parser):
        parser.add_argument('--start',
                            action='store',
                            metavar='YYYY-MM-DD',
                            default='1900-01-01',
                            help='Start of time range',
                            type=valid_date)

        parser.add_argument('--end',
                            action='store',
                            metavar='YYYY-MM-DD',
                            default='2100-12-31',
                            help='End of time range',
                            type=valid_date)

        parser.add_argument('--extent',
                            action='store',
                            metavar=('MIN_LON', 'MAX_LON', 'MIN_LAT', 'MAX_LAT'),
                            default=None,
                            help='Spatial extent',
                            type=float,
                            nargs=4)

        parser.add_argument('--geojson',
                            action='store',
                            metavar='GeoJSON',
                            default=None,
                            help='Filename of GeoJSON with polygon for spatial search',
                            type=str)

        parser.add_argument('--mask',
                            action='store',
                            default='',
                            help='Wildcard for filtering on filenames',
                            type=str)

        parser.add_argument('--force', action='store_true',
                            help='Force processing')

        parser.add_argument('--limit',
                            action='store',
                            default=None,
                            type=int,
                            help='Number of entries to process')

    def geometry_from_options(self, extent=None, geojson=None, **kwargs):
        """ Generate geometry to use in spatial search

        If extent is not None, return Polygon generated as POLYGON(()) with min/max lon/lat
        If geojson is not None, return Polygon loaded from the GeoJSON file
        Otherwise, return None

        Parameters
        ----------
        extent : [float, float, float, float]
            Values of min_lon, max_lon, min_lat, max_lat
        geojson : str
            Filename with Polygon GeoJSON
        **kwargs : dict
            other options from input arguments

        Returns
        -------
        geometry : geos.Polygon or None
        """
        polygon = None

        if extent is not None:
            # generate polygon from input extent parameter
            polygon = Polygon([ [extent[0], extent[2]],
                                [extent[1], extent[2]],
                                [extent[1], extent[3]],
                                [extent[0], extent[3]],
                                [extent[0], extent[2]]])
        elif geojson is not None and os.path.exists(geojson):
            # try to load GeoJSON and generate valid polygon
            with open(geojson, 'rt') as f:
                geojson = f.read().strip()
            try:
                polygon = GEOSGeometry(geojson)
            except (ValueError, GDALException, GEOSException):
                raise ValueError('Failed to read valid GeoJSON from %s'%options['geojson'])
            if not isinstance(polygon, Polygon):
                raise ValueError('Incorrect geometry type in GeoJSON %s'%options['geojson'])

        return polygon

    def find_datasets(self, **options):
        """ Find datasets that match input parameters

        Parameters
        ----------
        options : dict
            start : datetime
            end : datetime
            mask : str
            force : bool
            limit : int

        Returns
        -------
            datasets : django.QuerySet
        """

        datasets = Dataset.objects.filter(
                time_coverage_start__gte=options['start'],
                time_coverage_start__lte=options['end'],
                dataseturi__uri__contains=options['mask']).order_by('time_coverage_start')

        geometry = self.geometry_from_options(**options)
        if geometry is not None:
            datasets = datasets.filter(
                (Q(geographic_location__geometry__overlaps=geometry) |
                 Q(geographic_location__geometry__within=geometry)))

        return datasets

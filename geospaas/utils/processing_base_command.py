import os
import glob
from datetime import datetime as dt

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry, Polygon, GEOSException
from django.contrib.gis.gdal import GDALException

from geospaas.catalog.models import Dataset

def valid_date(s):
    """ Validate input datestring """
    try:
        return dt.strptime(s, "%Y-%m-%d")
    except:# ValueError:
        raise CommandError("Not a valid date: '{0}'.".format(s))


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
                            help='Start of time range',)
                            #type=valid_date) # such validation doesn't work with Django ...

        parser.add_argument('--end',
                            action='store',
                            metavar='YYYY-MM-DD',
                            default='2100-12-31',
                            help='End of time range',)
                            #type=valid_date) # such validation doesn't work with Django ...

        parser.add_argument('--extent',
                            action='store',
                            metavar=('MIN_LON', 'MAX_LON', 'MIN_LAT', 'MAX_LAT'),
                            default=None,
                            help='Spatial extent',
                            type=float,
                            nargs=4)

        parser.add_argument('--geojson',
                            action='store',
                            metavar='FILENAME',
                            default=None,
                            help='Filename of GeoJSON with polygon for spatial search',
                            type=str)

        parser.add_argument('--mask',
                            action='store',
                            default='',
                            help='Return only the datasets that have MASK in filename',
                            type=str)

        parser.add_argument('--force', action='store_true',
                            help='Force processing of all found datasets')

        parser.add_argument('--limit',
                            action='store',
                            default=None,
                            type=int,
                            help='Number of found datasets to process')

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
        elif geojson is not None:
            if not os.path.exists(geojson):
                raise CommandError('GeoJSON file %s was not found!' % geojson)
            # try to load GeoJSON and generate valid polygon
            with open(geojson, 'rt') as f:
                geojson = f.read().strip()
            try:
                polygon = GEOSGeometry(geojson)
            except (ValueError, GDALException, GEOSException):
                raise CommandError('Failed to read valid GeoJSON from %s' % geojson)

        return polygon

    def find_datasets(self, start='1900-01-01',
                            end='2100-12-31',
                            extent=None,
                            geojson=None,
                            mask='',
                            **kwargs):
        """ Find datasets that match input parameters

        Parameters
        ----------
        start : str
            Start of time range 'YYYY-MM-DD'
        end : str
            End of time range 'YYYY-MM-DD'
        extent : [float, float, float, float]
            Spatial extent ('MIN_LON', 'MAX_LON', 'MIN_LAT', 'MAX_LAT')
        geojson : str
            Filename of GeoJSON with polygon for spatial search
        mask : str
            Return only the datasets that have MASK in filename

        Returns
        -------
            datasets : django.QuerySet

        """
        start = valid_date(start)
        end = valid_date(end)
        datasets = Dataset.objects.filter(
                time_coverage_start__gte=start,
                time_coverage_start__lte=end,
                dataseturi__uri__contains=mask).order_by('time_coverage_start')

        geometry = self.geometry_from_options(extent=extent, geojson=geojson)
        if geometry is not None:
            datasets = datasets.filter(geographic_location__geometry__intersects=geometry)

        return datasets

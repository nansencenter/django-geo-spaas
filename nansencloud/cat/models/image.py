from __future__ import absolute_import

import warnings
import os, traceback
import pytz
import datetime
from dateutil.parser import parse

from nansat import Nansat, np
from nansat.tools import WrongMapperError, NansatReadError

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.db import models
from django.contrib.gis.db.models.query import GeoQuerySet

from nansencloud.cat.models.models import Status, Sensor, Satellite, SourceFile, Band, Location


class NotImageError(Exception):
    '''Error for handling files that are not Images (i.e., cannot be opened
    with Nansat)'''
    pass

class ImageQuerySet(GeoQuerySet):
    def sourcefiles(self):
        ''' Get list of full path/file names '''
        return [os.path.join(p, f) for p,f in self.values_list('sourcefile__path__address', 'sourcefile__name')]

    def new_sourcefiles(self, old_sourcefiles):
        ''' Get filenames which are not in old_filenames'''
        return frozenset(old_sourcefiles).difference(self.sourcefiles())


class ImageManager(models.GeoManager):
    '''Overwrite some methods of GeoManager'''
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def sourcefiles(self):
        return self.get_queryset().sourcefiles()

    def new_sourcefiles(self, old_filename):
        return self.get_queryset().new_sourcefiles(old_filename)

    def get_or_create(self, *args, **kwargs):
        ''' Create an instance of :model:`cat.Image` given the full
        path to a Nansat readable product`

        Parameters
        ----------
        fullpath : full filename and path to a Nansat readable product

        Returns
        -------
            image : :model:`cat.Image`
                either successfully created or fetched from the database
            create : bool
                indicator if image was create (True) or fethced (False)
        '''
        nborder_points = kwargs.pop('nPoints', None)

        # if fullpath is not provided, fallback to default method
        if len(args) != 1:
            return super(models.GeoManager, self).get_or_create(*args, **kwargs)

        fullpath = args[0]
        if not type(fullpath) in [str, unicode]:
            raise Exception('Input should be filename as str')
        if not os.path.exists(fullpath):
            raise IOError('%s does not exist!' % fullpath)

        mapper = kwargs.get('mapper', '')

        try:
            # open file with Nansat
            n = Nansat(fullpath, mapperName=mapper)
        except NansatReadError as e:
            # This cancels setting the status of a file if it can't be opened
            # with nansat
            raise type(e)(e.message+': '+fullpath) # re-raises the error

        try:
            return self.create_from_nansat(n, fullpath, nborder_points)
        except Exception as e:
            raise type(e)(e.message+': '+fullpath) # re-raises the error

    def create_from_nansat(self, n, fullpath, nborder_points=None):
        ''' Create Image from Nansat object and full path
        Parameters:
        -----------
            n : Nansat object
            fullpath : string with full path to input file
        Returns:
        --------
            image : Image object
            create : bool
                Was the Image created? (or fetched from database)
        '''

        # convert string sourcefile and path into SourceFile and Location
        sourcefile = SourceFile.objects.get_or_create(fullpath)[0]

        # fetch or create Image
        try:
            image = Image.objects.get(sourcefile=sourcefile)
            create = False
        except Image.DoesNotExist:
            image = Image(sourcefile=sourcefile)
            create = True
        else:
            # return image from the database
            return image, create

        # fetch all data from the file
        image.mapper = n.mapper
        image.status = Status.objects.get_or_create(
                            status=Status.GOOD_STATUS,
                            message="File is readable with Nansat")[0]

        # fetch relevant info from metadata (NB: this will override any fields
        # set during object creation but this should be safer)
        image.satellite = Satellite.objects.get_or_create(
                name=str(n.get_metadata('satellite')))[0]
        image.sensor = Sensor.objects.get_or_create(
                name=str(n.get_metadata('sensor')))[0]
        image.start_date = parse(n.get_metadata('start_date')+
                '+00:00').astimezone(pytz.utc)
        image.stop_date = parse(n.get_metadata('stop_date')+
                '+00:00').astimezone(pytz.utc)
        if nborder_points:
            image.border = GEOSGeometry(n.get_border_wkt(nPoints=nborder_points))
        else:
            image.border = GEOSGeometry(n.get_border_wkt())

        image.save()
        return image, create


class Image(models.Model):
    """ Stores a single dataset that can be read with Nansat,

    related to
    :model:`cat.SourceFile`,
    :model:`cat.Location`,
    :model:`cat.Status`,
    :model:`cat.Sensor`.
    :model:`cat.Satellite`.
    :model:`cat.Band`.
    """

    sourcefile = models.ForeignKey(SourceFile, unique=True)
    status = models.ForeignKey(Status, blank=True, null=True) # blank and null to allow backward migration
    sensor = models.ForeignKey(Sensor, blank=True, null=True)
    satellite = models.ForeignKey(Satellite, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    stop_date = models.DateTimeField(blank=True, null=True)
    mapper = models.CharField(max_length=100, blank=True)

    # GeoDjango-specific: a geometry field (PolygonField)
    border = models.PolygonField(null=True, blank=True)

    objects = ImageManager()

    def border2str(self):
        ''' Generate Leaflet JavaScript defining the border polygon'''
        borderStr = '['
        for coord in self.border.coords[0]:
            borderStr += '[%f, %f],' % coord[::-1]
        borderStr += "]"
        return borderStr

    def get_nansat(self, mapper=''):
        ''' Return Nansat object of the file '''
        return Nansat(str(self.sourcefile.full_path()), mapperName=mapper)

    def save(self, *args, **kwargs):
        ''' Check all fields, uniquness in the Image table and save

        Usage:
            i = Image.create(...)
            i.save()
        '''
        # test all fields before saving
        self.full_clean()
        super(Image, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.sourcefile.name


from __future__ import absolute_import

import warnings
import os, traceback
import pytz
import datetime
from dateutil.parser import parse

from nansat import Nansat, np
from nansat.tools import WrongMapperError, GDALError

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.db import models
from django.contrib.gis.db.models.query import GeoQuerySet

from cat.models.models import Status, Sensor, Satellite, SourceFile, Band, Location

class ImageQuerySet(GeoQuerySet):
    def sourcefiles(self):
        ''' Get list of full path/file names '''
        return [os.path.join(p, f) for p,f in self.values_list('sourcefile__location__address', 'sourcefile__name')]

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
        mapper = kwargs.get('mapper', '')

        if not type(fullpath) in [str, unicode]:
            raise Exception('Input should be filename as str')

        if not os.path.exists(fullpath):
            raise IOError('%s does not exist!' % fullpath)

        # convert string sourcefile and path into SourceFile and Location
        sourcefile = SourceFile.objects.get_or_create(fullpath)[0]

        # fetch or create an Image
        try:
            image = Image.objects.get(sourcefile=sourcefile)
            create = False
        except Image.DoesNotExist:
            image = Image(sourcefile=sourcefile)
            create = True
            # presave image for adding Bands later on
            image.save()
        else:
            # return image from the database
            return image, create

        # open file with Nansat
        try:
            n = image.get_nansat(mapper)
        except:   ### WARNING: any error is swallowed here... Should be fixed.
            # if file is not openable, warn, set status to Bad and return
            warnings.warn('\n\n Cannot get Nansat object from %s !! \n\n' % image.sourcefile)
            image.status = Status.objects.get_or_create(
                                status=Status.BAD_STATUS,
                                message=traceback.format_exc())[0]
            image.save()
            return image, create

        # if file is openable with Nansat
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

        # add Bands with essential info
        nBands = n.bands()
        for bandNumber in nBands:
            # get SourceFilename and make SourceFile and Location
            fullpath = nBands[bandNumber]['SourceFilename']

            # skip non existing or memory bands 
            # OBS: This excludes all zipped products and possibly other bands
            # as well - should be rethought...
            if not os.path.exists(fullpath):
                continue
            if fullpath.startswith('/vsimem'):
                continue

            sourcefile = SourceFile.objects.get_or_create(fullpath)[0]

            # get other relevant information
            sourceband = int(nBands[bandNumber]['SourceBand'])
            name = nBands[bandNumber].get('name', 'unknown')
            standard_name = nBands[bandNumber].get('standard_name', 'unknown')

            # create Band and save
            band = Band(sourcefile=sourcefile,
                        sourceband=sourceband,
                        name=name,
                        standard_name=standard_name)
            band.save()

            # add to bands
            image.bands.add(band)

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
    bands = models.ManyToManyField(Band)

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
        return Nansat(str(self.sourcefile), mapperName=mapper)

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


from __future__ import absolute_import

import os, traceback
import pytz
import datetime
from dateutil.parser import parse

import numpy as np

try:
    from osgeo import gdal
except:
    import gdal

from nansat import Nansat, Figure
from nansat.tools import WrongMapperError, GDALError

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.db import models

class BadSourceFileError(Exception):
    pass

class LocationManager(models.Manager):
    def get_or_create(self, *args, **kwargs):
        ''' Create and save SourceFilename if full name is given

        Usage
        -----
            # STANDARD
            f, cr = Location.objects.get_or_create(name=path, type=0)
            # CUSTOM
            f, cr = Location.objects.get_or_create(path)

        Parameters
        ----------
            path : str or unicode
                Full address of a source file. Can be either path on local
                filesystem or FTP, HTTP, OpenDAP address
        Returns
        -------
            location : Location
                the created object
            create : bool
                True, if a new object was created; False if fetched from DB

        '''

        if len(args) != 1 or len(kwargs) != 0:
            # if keyword args are provided, fallback to default method
            return super(models.Manager, self).get_or_create(*args, **kwargs)

        path = args[0]

        if type(path) not in [str, unicode]:
            raise Exception('''
                    Input should be str or unicode.
                    Found %s instead ''' % str(type(path)))

        # create location object
        if path.startswith('/'):
            location, cr = Location.objects.get_or_create(address=path,
                    type=Location.FS)
        elif path.startswith('ftp://'):
            location, cr = Location.objects.get_or_create(address=path,
                    type=Location.FTP)
        elif path.startswith('http://'):
            location, cr = Location.objects.get_or_create(address=path,
                    type=Location.HTTP)
        elif path.startswith('https://'):
            location, cr = Location.objects.get_or_create(address=path,
                    type=Location.HTTPS)
        else:
            raise Exception(' Unknow type of Location: %s ' % path)

        return location, cr


class Location(models.Model):
    ''' Location of the SourceFile, filesystem, FTP, HTTP or OpenDAP'''
    FS   = 0
    DAP  = 1
    FTP  = 2
    HTTP = 3
    HTTPS = 4

    LOCATION_CHOICES = (
        (FS,   'Filesystem'),
        (DAP,  'OpenDAP'),
        (FTP,  'FTP'),
        (HTTP, 'HTTP'),
        (HTTPS, 'HTTPS'),
    )

    type = models.IntegerField(choices=LOCATION_CHOICES, default=FS)
    address = models.CharField(max_length=300)

    objects = LocationManager()

    def __unicode__(self):
        return self.address

class SourceFileManager(models.Manager):
    def get_or_create(self, *args, **kwargs):
        ''' Create SourceFile from fullpath

        Usage
        -----
            sf = SourceFile.objects.get_or_create(fullpath)
            sf = SourceFile.objects.get_or_create(fullpath, force=True)

        '''
        if len(args) != 1:
            # if keyword args are provided, fallback to default method
            return super(models.Manager, self).get_or_create(*args, **kwargs)

        fullpath = args[0]

        if type(fullpath) not in [str, unicode]:
            raise Exception('''
                    Input should be str or unicode.
                    Found %s instead ''' % str(type(fullpath)))

        if not os.path.exists(fullpath) and ('force' not in kwargs or not kwargs['force']):
            raise Exception(''' %s does not exist ''' % fullpath)

        path, name = os.path.split(fullpath)
        path = Location.objects.get_or_create(path)[0]

        return super(models.Manager, self).get_or_create(name=name,
                                                         path=path)

class SourceFile(models.Model):
    ''' Source of Image Band'''
    name = models.CharField(max_length=200)
    path = models.ForeignKey(Location, blank=True, null=True, related_name='sourcefile_path')
    urls = models.ManyToManyField(Location, blank=True, null=True, related_name='sourcefile_locations')

    objects = SourceFileManager()

    def __unicode__(self):
        return self.name

    def full_path(self):
        return os.path.join(self.path.address, self.name)

    def full_http(self):
        return os.path.join(self.urls.all()[0].address, self.name)
    #def get_absolute_url(self, type):
    # return the url of the file, optionally specifying the type of url (e.g.,
    # http, opendap, ftp, etc.)


class SensorManager(models.Manager):
    def get_or_create(self, *args, **kwargs):
        ''' Capitalize name before calling standard get_or_create '''
        # capitalize name
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].capitalize()
        # call standard method
        return super(models.Manager, self).get_or_create(*args, **kwargs)


class Sensor(models.Model):
    ''' Name of the sensor'''
    name = models.CharField(max_length=200)
    objects = SensorManager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super(Sensor, self).save(*args, **kwargs)


class Satellite(models.Model):
    '''Name of the satellite '''
    name = models.CharField(max_length=200)
    objects = SensorManager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super(Satellite, self).save(*args, **kwargs)


# Status model hints:
# http://www.b-list.org/weblog/2007/nov/02/handle-choices-right-way/
class Status(models.Model):
    GOOD_STATUS = 0
    BAD_STATUS = 1
    STATUS_CHOICES = (
        (GOOD_STATUS, 'Good'),
        (BAD_STATUS, 'Bad'),
    )
    status  = models.IntegerField(choices=STATUS_CHOICES, default=GOOD_STATUS)
    message = models.TextField(default='')

    def __unicode__(self):
        return {0: 'OK', 1: 'BAD'}[self.status]


class Band(models.Model):
    ''' Information about band that enables creation of VRT'''
    sourcefile    = models.ForeignKey(SourceFile)
    sourceband    = models.IntegerField()
    name          = models.CharField(max_length=100, blank=True)
    standard_name = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return '%s[%s]' % (self.sourcefile, self.name)


    def get_data(self, step=1):
        ''' Get array with data from the band using GDAL '''
        ds = gdal.Open(str(self.sourcefile))
        b = ds.GetRasterBand(self.sourceband)
        return b.ReadAsArray()[::step, ::step]

    def get_image(self, step=10):
        ''' Get PIL.Image object from the band '''
        data = self.get_data(step=step)
        fig = Figure(data)
        fig.process(cmin=data.min(), cmax=data.max())
        return fig.pilImg


class Search(models.Model):
    ''' Search parameters '''
    sdate = models.DateTimeField(blank=True, null=True) # when was search
    date0 = models.DateField()                          # from this date
    date1 = models.DateField()                          # until this date
    status    = models.ForeignKey(Status, blank=True, null=True)
    satellite = models.ForeignKey(Satellite, blank=True, null=True)
    sensor    = models.ForeignKey(Sensor, blank=True, null=True)

    # GeoDjango-specific: a geometry field (PolygonField), and
    # overriding the default manager with a GeoManager instance.
    polygon = models.PolygonField(blank=True, null=True) # intersect this poly
    objects = models.GeoManager()

    def __unicode__(self):
        poly = ''
        if self.polygon is not None:
            poly = str(self.polygon.num_points)

        return self.sdate.strftime('%Y-%m-%d %H:%M ') + poly


from django.db import models
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage

class GeographicLocation(geomodels.Model):
    geometry = geomodels.GeometryField()

    objects = geomodels.GeoManager()


class Source(models.Model):
    SATELLITE = 'Satellite'
    INSITU = 'In-situ'
    MODEL = 'Model'
    SOURCE_TYPES = ((SATELLITE, SATELLITE), (INSITU, INSITU), (MODEL, MODEL))

    type = models.CharField(max_length=15, choices=SOURCE_TYPES)
    platform = models.CharField(max_length=100, default='',
        help_text='Data recording platform.')
    instrument = models.CharField(max_length=15, default='',
        help_text='The sensor used to record measurements.')
    specs = models.CharField(max_length=50, default='',
        help_text='Further specifications of the source.')


class Dataset(models.Model):
    source = models.ForeignKey(Source)
    geolocation = models.ForeignKey(GeographicLocation)
    time_coverage_start = models.DateTimeField()
    time_coverage_end = models.DateTimeField()


class DataLocation(models.Model):
    LOCALFILE = 'LOCALFILE'
    OPENDAP = 'OPENDAP'
    FTP = 'FTP'
    HTTP = 'HTTP'
    HTTPS = 'HTTPS'
    WMS = 'WMS'
    WFS = 'WFS'
    PROTOCOL_CHOICES = ((LOCALFILE, LOCALFILE),
                        (OPENDAP, OPENDAP),
                        (FTP,FTP),
                        (HTTP,HTTP),
                        (HTTPS,HTTPS),
                        (WMS,WMS),
                        (WFS,WFS),
                       )

    protocol = models.CharField(max_length=15, choices=PROTOCOL_CHOICES)
    uri = models.URLField(max_length=200, unique=True)
    dataset = models.ForeignKey(Dataset)

class Product(models.Model):
    short_name = models.CharField(max_length=10)
    standard_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=200)
    units = models.CharField(max_length=10)
    dataset = models.ForeignKey(Dataset)
    location = models.ForeignKey(DataLocation)

class DatasetRelationship(models.Model):
    child = models.ForeignKey(Dataset, related_name='parents')
    parent = models.ForeignKey(Dataset, related_name='children')

"""
# Files are stored locally, not uploaded
# Optionally we may write a custom file storage system (may be needed with
# openstack)
fs = FileSystemStorage(location='/vagrant/shared/test_data')
class DataLocation(models.Model):
    file = models.FileField(storage=fs, default=None, null=True)
    dap = models.URLField(default=None, null=True)
    ftp = models.URLField(default=None, null=True)
    http = models.URLField(default=None, null=True)
    wms = models.URLField(default=None, null=True)
    wfs = models.URLField(default=None, null=True)

    def save(self):
        # Check that at least one field is populated
        if not any([self.file, self.dap, self.ftp, self.http, self.wms,
            self.wfs]):
            raise PermissionDenied
        super(DataLocation, self).save()
"""

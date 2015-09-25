from django.db import models
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage

class Dataset(models.Model):
    source = models.OneToOneField('Source')
    geolocation = models.OneToOneField('GeographicLocation')
    variables = models.ManyToManyField('Variable')
    data_location = models.ManyToManyField('DataLocation')
    time_coverage_start = models.DateTimeField()
    time_coverage_end = models.DateTimeField()

class Source(models.Model):
    SAT = 'Satellite'
    INSITU = 'In-situ'
    MODEL = 'Model'
    SOURCE_TYPES = ((SAT, SAT), (INSITU, INSITU), (MODEL, MODEL))

    type = models.CharField(max_length=15, choices=SOURCE_TYPES)
    platform = models.CharField(max_length=100)
    tool = models.CharField(max_length=50, 
        help_text='The tool could be instrument, model version, etc.')

class GeographicLocation(geomodels.Model):
    GRID = 'Grid'
    POINT = 'Point'
    TRAJECTORY = 'Trajectory'
    GEOGRAPHIC_TYPES = ((GRID, GRID), (POINT, POINT), (TRAJECTORY, TRAJECTORY))

    geometry = geomodels.GeometryField()
    type = models.CharField(max_length=15, choices=GEOGRAPHIC_TYPES)

    objects = geomodels.GeoManager()

class Variable(models.Model):
    short_name = models.CharField(max_length=10)
    standard_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=200)
    units = models.CharField(max_length=10)

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

import os

from django.db import models
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage

from nansencloud.gcmd_keywords.models import Platform, Instrument

class GeographicLocation(geomodels.Model):
    geometry = geomodels.GeometryField()

    objects = geomodels.GeoManager()

    def __str__(self):
        return str(self.geometry.geom_type) + str(self.geometry.num_points)


class Source(models.Model):
    platform = models.ForeignKey(Platform)
    instrument = models.ForeignKey(Instrument)
    specs = models.CharField(max_length=50, default='',
        help_text='Further specifications of the source.')

    class Meta:
        unique_together = (("platform", "instrument"),)

    def __str__(self):
        return '%s/%s' % (self.platform, self.instrument)

# Must be filled with standard variables, perhaps also moved to another app
class Parameter(models.Model):
    short_name = models.CharField(max_length=10)
    standard_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=200)
    units = models.CharField(max_length=10)

    #gcmd_science_keyword = models.OneToOneField(ScienceKeyword)

    def __str__(self):
        return '%s/%s' % (self.location, self.short_name)

class Dataset(models.Model):
    entry_title = models.CharField(max_length=100)
    parameters = models.ManyToManyField(Parameter, through='DatasetParameter')
    ISO_topic_category =
    data_center = models.ForeignKey(DataCenter)
    summary = models.TextField()
    metadata_name = models.CharField(max_length=50, default='CEOS IDN DIF')
    metadata_version = 


    time_coverage_start = models.DateTimeField()
    time_coverage_end = models.DateTimeField()

    source = models.ForeignKey(Source)
    geolocation = models.ForeignKey(GeographicLocation)


    def __str__(self):
        return '%s' %self.entry_title

class DatasetParameter(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)

    def __str__(self):
        return '%s:%s' %(self.dataset, self.parameter)

class VisualizationParameter(models.Model):
    visualization = models.ForeignKey('Visualization', on_delete=models.CASCADE)
    ds_parameter = models.ForeignKey(DatasetParameter, on_delete=models.CASCADE)

class Visualization(models.Model):
    
    uri = models.URLField()
    # A visualization may contain more than one parameter, and the same
    # parameter can be visualized in many ways..
    parameters = models.ManyToManyField(DatasetParameter,
            through=VisualizationParameter)

    #def get_absolut_url(self):


class DatasetLocation(models.Model):

    uri = models.URLField(max_length=200, unique=True)
    dataset = models.ForeignKey(Dataset)

    def __str__(self):
        return '%s: %s'%(self.dataset, os.path.split(self.uri)[1])

    def protocol(self):
        return self.uri.split(':')[0]

class DatasetRelationship(models.Model):
    child = models.ForeignKey(Dataset, related_name='parents')
    parent = models.ForeignKey(Dataset, related_name='children')


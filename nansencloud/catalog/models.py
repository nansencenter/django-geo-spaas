import os

from django.db import models
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.utils.translation import ugettext as _

from nansencloud.gcmd_keywords.models import ScienceKeyword
from nansencloud.gcmd_keywords.models import Platform
from nansencloud.gcmd_keywords.models import Instrument
from nansencloud.gcmd_keywords.models import ISOTopicCategory
from nansencloud.gcmd_keywords.models import DataCenter
from nansencloud.gcmd_keywords.models import Location as GCMDLocation
from nansencloud.gcmd_keywords.models import HorizontalDataResolution
from nansencloud.gcmd_keywords.models import VerticalDataResolution
from nansencloud.gcmd_keywords.models import TemporalDataResolution

class GeographicLocation(geomodels.Model):
    geometry = geomodels.GeometryField()

    objects = geomodels.GeoManager()

    def __str__(self):
        return str(self.geometry.geom_type) + str(self.geometry.num_points)


class Source(models.Model):
    platform = models.ForeignKey(Platform)
    instrument = models.ForeignKey(Instrument)
    specs = models.CharField(max_length=50, default='',
        help_text=_('Further specifications of the source.'))

    class Meta:
        unique_together = (("platform", "instrument"),)

    def __str__(self):
        return '%s/%s' % (self.platform, self.instrument)

class Role(models.Model):
    INVESTIGATOR = 'Investigator'
    TECH_CONTACT = 'Technical Contact' # I interpret this as the data center contact
    DIF_AUTHOR = 'DIF Author'
    ROLE_CHOICES = ((INVESTIGATOR, INVESTIGATOR), (TECH_CONTACT, TECH_CONTACT),
            (DIF_AUTHOR, DIF_AUTHOR))
    personnel = models.ForeignKey(Personnel)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Personnel(models.Model):
    '''
    This class follows the fields specified in
    http://gcmd.nasa.gov/add/difguide/personnel.html, except those already
    present in django.contrib.auth.User
    We may use django-userena to handle Personnel and other users..
    '''
    phone = models.CharField(max_length=80)
    fax = models.CharField(max_length=80)
    address = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    province_or_state = models.CharField(max_length=80)
    postal_code = models.CharField(max_length=80)
    country = models.CharField(max_length=80)

    class Meta:
        permissions = (
                ("accessLevel0", "Can access all data"),
                ("accessLevel1", "Can access data at own data center"),
                ("accessLevel2", "Can access public data only"),
            )

# Must be filled with standard variables
class Parameter(models.Model):
    ''' This table resembles the well-known-variables in nansat (wkv.xml) -
    perhaps there should be an exact mapping between this table and the
    wkv.xml-file...
    '''
    short_name = models.CharField(max_length=10)
    long_name = models.CharField(max_length=200)
    units = models.CharField(max_length=10)

    # blank=True and null=True to allow for variables not in the gcmd science
    # keywords table:
    gcmd_science_keyword = models.OneToOneField(ScienceKeyword, blank=True,
            null=True)
    # blank=True and null=True to allow for variables not in the CF standard
    # names table:
    cf_standard_name = models.OneToOneField(CFStandardName, blank=True,
            null=True)

    def __str__(self):
        return '%s' %self.short_name

class Dataset(models.Model):
    ''' 
    The Dataset model contains fields from the GCMD DIF conventions that are
    used for indexing and search.

    For a full description of the DIF format, see
    http://gcmd.nasa.gov/add/difguide/index.html and
    http://gcmd.nasa.gov/add/difguide/WRITEADIF.pdf

    Fields:
    -------
    entry_title : CharField
    parameters: ManyToManyField to Parameter through DatasetParameter
    ISO_topic_category : ForeignKey to ISOTopicCategory
    data_center : ForeignKey to DataCenter
    summary : TextField
            In addition to some general information, the summary should also
            contain information about the project from/for which the data was
            collected/created
    source : ForeignKey to Source
            Contains information about the instrument and platform by which the
            data was collected
    time_coverage_start : DateTimeField
    time_coverage_end : DateTimeField
    geographic_location : ForeignKey to GeographicLocation
    gcmd_location : ForeignKey to gcmd_keywords.models.Location
    access_constraints : CharField
            Determines the access level of the Dataset: Limited, In-house, or
            Public

    '''
    ACCESS_LEVEL0 = 'accessLevel0'
    ACCESS_LEVEL1 = 'accessLevel1'
    ACCESS_LEVEL2 = 'accessLevel2'
    ACCESS_CHOICES = (
            (ACCESS_LEVEL0, _('Limited')),
            (ACCESS_LEVEL1, _('In-house')),
            (ACCESS_LEVEL2, _('Public')),
        )

    # DIF required fields
    entry_title = models.CharField(max_length=220)
    parameters = models.ManyToManyField(Parameter, through='DatasetParameter')
    ISO_topic_category = models.ForeignKey(ISOTopicCategory)
    data_center = models.ForeignKey(DataCenter)
    summary = models.TextField()

    # DIF highly recommended fields
    source = models.ForeignKey(Source, blank=True, null=True)
    time_coverage_start = models.DateTimeField(blank=True, null=True)
    time_coverage_end = models.DateTimeField(blank=True, null=True)
    geographic_location = models.ForeignKey(GeographicLocation, blank=True, null=True)
    gcmd_location = models.ForeignKey(GCMDLocation, blank=True, null=True)
    access_constraints = models.CharField(max_length=50,
            choices=ACCESS_CHOICES, blank=True, null=True)

    def __str__(self):
        return '%s/%s/%s' % (self.source.platform, self.source.instrument,
                self.time_coverage_start.isoformat())

# Keep this for reference if we want to add it
#class DataResolution(models.Model):
#    dataset = models.ForeignKey(Dataset)
#    latitude_resolution = models.CharField(max_length=50)
#    longitude_resolution = models.CharField(max_length=50)
#    horizontal_resolution = models.CharField(max_length=220)
#    horizontal_resolution_range = models.ForeignKey(HorizontalDataResolution)
#    vertical_resolution = models.CharField(max_length=220)
#    vertical_resolution_range = models.ForeignKey(VerticalDataResolution)
#    temporal_resolution = models.CharField(max_length=220)
#    temporal_resolution_range = models.ForeignKey(TemporalDataResolution)

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


class DatasetURI(models.Model):

    uri = models.URLField(max_length=200, unique=True)
    dataset = models.ForeignKey(Dataset)

    def __str__(self):
        return '%s: %s'%(self.dataset, os.path.split(self.uri)[1])

    def protocol(self):
        return self.uri.split(':')[0]

class DatasetRelationship(models.Model):
    child = models.ForeignKey(Dataset, related_name='parents')
    parent = models.ForeignKey(Dataset, related_name='children')


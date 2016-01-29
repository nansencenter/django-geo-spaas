import os

from django.db import models
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage

from nansencloud.gcmd_keywords.models import Platform
from nansencloud.gcmd_keywords.models import Instrument
from nansencloud.gcmd_keywords.models import ISOTopicCategory
from nansencloud.gcmd_keywords.models import DataCenter
from nansencloud.gcmd_keywords.models import Location
from nansencloud.gcmd_keywords.models import Project
from nansencloud.gcmd_keywords.models import HorizontalDataResolution
from nansencloud.gcmd_keywords.models import VerticalDataResolution
from nansencloud.gcmd_keywords.models import TemporalDataResolution

class SpatialCoverage(geomodels.Model):
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

class Role(models.Model):
    INVESTIGATOR = 'Investigator'
    TECH_CONTACT = 'Technical Contact'
    DIF_AUTHOR = 'DIF Author'
    ROLE_CHOICES = ((INVESTIGATOR, INVESTIGATOR), (TECH_CONTACT, TECH_CONTACT),
            (DIF_AUTHOR, DIF_AUTHOR))
    personnel = models.ForeignKey(Personnel)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Personnel(models.Model):
    # This class follows the fields specified in
    # http://gcmd.nasa.gov/add/difguide/personnel.html, except those already
    # present in django.contrib.auth.User
    # We may use django-userena to handle Personnel and other users..
    phone = models.CharField(max_length=80)
    fax = models.CharField(max_length=80)
    address = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    province_or_state = models.CharField(max_length=80)
    postal_code = models.CharField(max_length=80)
    country = models.CharField(max_length=80)

class Dataset(models.Model):
    ''' 
    For a full description of the DIF format, see
    http://gcmd.nasa.gov/add/difguide/index.html and
    http://gcmd.nasa.gov/add/difguide/WRITEADIF.pdf
    '''
    COMPLETE = 'Complete'
    INWORK = 'In Work'
    PLANNED = 'Planned'
    PROGRESS_CHOICES = ((COMPLETE, COMPLETE), (INWORK, INWORK), (PLANNED,
        PLANNED))

    # Required fields
    entry_title = models.CharField(max_length=220)
    parameters = models.ManyToManyField(Parameter, through='DatasetParameter')
    ISO_topic_category = models.ForeignKey(ISOTopicCategory)
    data_center = models.ForeignKey(DataCenter)
    summary = models.TextField()
    metadata_name = models.CharField(max_length=50, default='CEOS IDN DIF')
    metadata_version = models.CharField(max_length=50, default='VERSION 9.9')

    # Highly recommended fields
    # data_set_citation's are included by foreignkey from DatasetCitation
    personnel = models.ForeignKey(Personnel, blank=True, null=True) # = contact person
    # Instrument and platform:
    source = models.ForeignKey(Source, blank=True, null=True)
    time_coverage_start = models.DateTimeField(blank=True, null=True)
    time_coverage_end = models.DateTimeField(blank=True, null=True)
    #paleo_temporal_coverage skipped
    spatial_coverage = models.ForeignKey(SpatialCoverage, blank=True, null=True)
    location = models.ForeignKey(Location, blank=True, null=True)
    # data_resolution's are included by foreignkey from DataResolution
    projects = models.ManyToManyField(Project, blank=True, null=True)
    quality = models.TextField(blank=True, null=True)
    access_constraints = models.TextField(blank=True, null=True)
    use_constraints = models.TextField(blank=True, null=True)
    distribution_media = models.CharField(max_length=80, blank=True, null=True)
    distribution_size = models.CharField(max_length=80, blank=True, null=True)
    distribution_format = models.CharField(max_length=80, blank=True, null=True)
    distribution_fee = models.CharField(max_length=80, blank=True, null=True)
    # Language list in  the ISO 639 language codes:
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    language = models.CharField(maX_length=80, default='English', blank=True,
            null=True)
    progress = models.CharField(max_length=31, choices=PROGRESS_CHOICES,
            blank=True, null=True)
    #related_url = models.ManyToManyField(RelatedURL, blank=True, null=True)

    # Recommended fields
    #DIF_revision_history included by ForeignKey from DIFRevisionHistory 
    # keyword
    #originating_center
    #references
    #parent_DIF
    #IDN_node
    #DIF_creation_date
    #last_DIF_revision_date
    #future_DIF_review_date
    #privacy_status
    #extended_metadata

    def __str__(self):
        return '%s' %self.entry_title

class DIFRevisionHistoryItem(models.Model):
    dataset = models.ForeignKey(Dataset)
    date = models.DateField()
    text = models.TextField()

class DataResolution(models.Model):
    dataset = models.ForeignKey(Dataset)
    latitude_resolution = models.CharField(max_length=50)
    longitude_resolution = models.CharField(max_length=50)
    horizontal_resolution = models.CharField(max_length=220)
    horizontal_resolution_range = models.ForeignKey(HorizontalDataResolution)
    vertical_resolution = models.CharField(max_length=220)
    vertical_resolution_range = models.ForeignKey(VerticalDataResolution)
    temporal_resolution = models.CharField(max_length=220)
    temporal_resolution_range = models.ForeignKey(TemporalDataResolution)

class DatasetCitation(models.Model):
    dataset = models.ForeignKey(Dataset)
    dataset_creator = models.ForeignKey(Personnel)
    dataset_editor = models.ForeignKey(Personnel)
    dataset_publisher = models.ForeignKey(DataCenter)
    #dataset_title = models.CharField(max_length=220) # Same as entry_title in Dataset
    dataset_series_name = models.CharField(max_length=220)
    dataset_release_date = models.DateField()
    dataset_release_place = models.CharField(max_length=80)
    version = models.Charfield(max_length=15)
    issue_identification = models.CharField(max_length=80)
    data_presentation_form = models.CharField(max_length=80)
    other_citation_details = models.CharField(max_length=220)
    dataset_DOI = models.CharField(max_length=220)
    online_resource = models.URLField(max_length=600)

    def __str__(self):
        return self.dataset_DOI
    

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


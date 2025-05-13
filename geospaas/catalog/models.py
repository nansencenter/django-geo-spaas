import os
import uuid

from django.contrib.gis.db import models as geomodels
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext as _

from geospaas.vocabularies.models import Parameter
from geospaas.vocabularies.models import Keyword

from geospaas.catalog.managers import DatasetURIManager
from geospaas.catalog.managers import FILE_SERVICE_NAME
from geospaas.catalog.managers import LOCAL_FILE_SERVICE


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


class Role(models.Model):
    INVESTIGATOR = 'Investigator'
    TECH_CONTACT = 'Technical Contact' # I interpret this as the data center contact
    DIF_AUTHOR = 'DIF Author'
    ROLE_CHOICES = ((INVESTIGATOR, INVESTIGATOR), (TECH_CONTACT, TECH_CONTACT),
            (DIF_AUTHOR, DIF_AUTHOR))
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


def validate_tag(tag):
    """Validate the tag data
    """
    if not isinstance(tag, dict):
        raise ValidationError('Tag must be a dict')


class Tag(models.Model):
    """Tag which can be associated to a dataset
    """
    data = models.JSONField(null=False, validators=(validate_tag,))


class Dataset(models.Model):
    '''
    The Dataset model contains fields from the GCMD DIF conventions that are
    used for indexing and search.

    For a full description of the DIF format, see
    http://gcmd.nasa.gov/add/difguide/index.html and
    http://gcmd.nasa.gov/add/difguide/WRITEADIF.pdf

    Fields:
    -------
    :entry_id: TextField.
        A unique dataset ID. Only alphanumeric characters are allowed.
    :entry_title: CharField
    :parameters: ManyToManyField to Parameter
    :ISO_topic_category: ForeignKey to ISOTopicCategory
    :data_center: ForeignKey to DataCenter
    :summary: TextField.
        In addition to some general information, the summary should also
        contain information about the project from/for which the data was
        collected/created
    :source: ForeignKey to Source
        Contains information about the instrument and platform by which the
        data was collected
    :time_coverage_start: DateTimeField
    :time_coverage_end: DateTimeField
    :geographic_location: ForeignKey to GeographicLocation
    :gcmd_location: ForeignKey to vocabularies.models.Location
    :access_constraints: CharField.
        Determines the access level of the Dataset: Limited, In-house, or Public
    '''
    ACCESS_LEVEL0 = 'accessLevel0'
    ACCESS_LEVEL1 = 'accessLevel1'
    ACCESS_LEVEL2 = 'accessLevel2'
    ACCESS_CHOICES = (
            (ACCESS_LEVEL0, _('Limited')),
            (ACCESS_LEVEL1, _('In-house')),
            (ACCESS_LEVEL2, _('Public')),
        )
    access_constraints = models.CharField(max_length=50,
            choices=ACCESS_CHOICES, blank=True, null=True)

    entry_id = models.TextField(unique=True, default=uuid.uuid4,
        validators=[
            RegexValidator(r'^[0-9a-zA-Z_.-]*$', 'Only alphanumeric characters are allowed.')
        ]
    )
    time_coverage_start = models.DateTimeField(blank=True, null=True)
    time_coverage_end = models.DateTimeField(blank=True, null=True)
    location = geomodels.GeometryField(blank=True, null=True)
    keywords = models.ManyToManyField(Keyword)
    tags = models.ManyToManyField(Tag)
    summary = models.TextField()
    entry_title = models.CharField(max_length=220)
    parameters = models.ManyToManyField(Parameter)

    def __str__(self):
        return '%s/%s/%s' % (self.source.platform, self.source.instrument,
                self.time_coverage_start.isoformat())


class DatasetURI(models.Model):

    name = models.CharField(max_length=20, default=FILE_SERVICE_NAME)
    service = models.CharField(max_length=20, default=LOCAL_FILE_SERVICE)
    uri = models.URLField(max_length=500,
            validators=[URLValidator(schemes=URLValidator.schemes + ['file'])])
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    objects = DatasetURIManager()
    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_dataset_uri', fields=['uri', 'dataset'])
        ]

    def __str__(self):
        return '%s: %s'%(self.dataset, os.path.split(self.uri)[1])

    def protocol(self):
        return self.uri.split(':')[0]


class DatasetRelationship(models.Model):
    child = models.ForeignKey(Dataset, related_name='parents', on_delete=models.CASCADE)
    parent = models.ForeignKey(Dataset, related_name='children', on_delete=models.CASCADE)

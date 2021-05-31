from django.db import models

from geospaas.vocabularies.managers import ParameterManager
from geospaas.vocabularies.managers import PlatformManager
from geospaas.vocabularies.managers import InstrumentManager
from geospaas.vocabularies.managers import DataCenterManager
from geospaas.vocabularies.managers import ScienceKeywordManager
from geospaas.vocabularies.managers import ProjectManager
from geospaas.vocabularies.managers import HorizontalDataResolutionManager
from geospaas.vocabularies.managers import VerticalDataResolutionManager
from geospaas.vocabularies.managers import TemporalDataResolutionManager
from geospaas.vocabularies.managers import ISOTopicCategoryManager
from geospaas.vocabularies.managers import LocationManager

# GCMD keywords loaded into the models in migrations/0001_initial.py using the
# nersc-metadata package

class Platform(models.Model):

    category = models.CharField(max_length=100)
    series_entity = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=250)

    objects = PlatformManager()

    def __str__(self):
        return str(self.short_name)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_platform', fields=[
                'category', 'series_entity', 'short_name', 'long_name'])
        ]


class Instrument(models.Model):

    category = models.CharField(max_length=100)
    instrument_class = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    subtype = models.CharField(max_length=100)
    short_name = models.CharField(max_length=60)
    long_name = models.CharField(max_length=200)

    objects = InstrumentManager()

    def __str__(self):
        return str(self.short_name)



    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_instrument', fields=[
                'category', 'instrument_class', 'type', 'subtype', 'short_name', 'long_name'])
        ]


class ISOTopicCategory(models.Model):
    '''
    The <ISO_Topic_Category> field is used to identify the keywords in the ISO
    19115 - Geographic Information Metadata (http://www.isotc211.org/) Topic
    Category Code List. It is a high-level geographic data thematic
    classification to assist in the grouping and search of available geographic
    data sets.

    Directory Interchange Format (DIF) Writer's Guide, 2015.
    Global Change Master Directory.
    National Aeronautics and Space Administration.
    [http://gcmd.nasa.gov/add/difguide/].
    '''
    name = models.CharField(max_length=100)
    # see http://gcmd.gsfc.nasa.gov/add/difguide/iso_topics.html for
    #description = models.TextField()

    objects = ISOTopicCategoryManager()

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.name)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_iso_topic_category', fields=['name'])
        ]


class DataCenter(models.Model):
    ''' The data center is needed to control data access and also for indexing
    to allow search.
    '''
    bucket_level0 = models.CharField(max_length=200)
    bucket_level1 = models.CharField(max_length=200)
    bucket_level2 = models.CharField(max_length=200)
    bucket_level3 = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=250)
    data_center_url = models.URLField()

    objects = DataCenterManager()

    def __str__(self):
        return str(self.short_name)

    def natural_key(self):
        return (self.short_name)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_data_center', fields=[
                'bucket_level0', 'bucket_level1', 'bucket_level2', 'bucket_level3',
                'short_name', 'long_name', 'data_center_url'])
        ]


class Location(models.Model):
    category = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    subregion1 = models.CharField(max_length=50)
    subregion2 = models.CharField(max_length=50)
    subregion3 = models.CharField(max_length=50)

    objects = LocationManager()

    def __str__(self):
        return str('%s %s' %(self.subregion2, self.subregion3))

    def natural_key(self):
        return (category, type, subregion1, subregion2,
            subregion3)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_location', fields=[
                'category', 'type', 'subregion1', 'subregion2', 'subregion3'])
        ]


class ScienceKeyword(models.Model):
    category = models.CharField(max_length=50)
    topic = models.CharField(max_length=50)
    term = models.CharField(max_length=80)
    variable_level_1 = models.CharField(max_length=80)
    variable_level_2 = models.CharField(max_length=80)
    variable_level_3 = models.CharField(max_length=80)
    detailed_variable = models.CharField(max_length=80)

    objects = ScienceKeywordManager()

    def __str__(self):
        return str('%s' %self.detailed_variable)

    def natural_key(self):
        return (self.category, self.topic, self.term, self.variable_level_1,
                self.variable_level_2, self.variable_level_3)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_science_keyword', fields=[
                'category', 'topic', 'term', 'variable_level_1', 'variable_level_2',
                'variable_level_3', 'detailed_variable'])
        ]


class Project(models.Model):
    bucket = models.CharField(max_length=6)
    short_name = models.CharField(max_length=80)
    long_name = models.CharField(max_length=220)

    objects = ProjectManager()

    def __str__(self):
        return str(self.short_name)

    def natural_key(self):
        return (self.bucket, self.short_name)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_project',
                                    fields=['bucket', 'short_name', 'long_name'])
        ]


class HorizontalDataResolution(models.Model):
    range = models.CharField(max_length=220)

    objects = HorizontalDataResolutionManager()

    def __str__(self):
        return str(self.range)

    def natural_key(self):
        return (self.range)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_horizontal_data_resolution', fields=['range'])
        ]


class VerticalDataResolution(models.Model):
    range = models.CharField(max_length=220)

    objects = VerticalDataResolutionManager()

    def __str__(self):
        return str(self.range)

    def natural_key(self):
        return (self.range)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_vertical_data_resolution', fields=['range'])
        ]


class TemporalDataResolution(models.Model):
    range = models.CharField(max_length=220)

    objects = TemporalDataResolutionManager()

    def __str__(self):
        return str(self.range)

    def natural_key(self):
        return (self.range)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_temporal_data_resolution', fields=['range'])
        ]


class Parameter(models.Model):
    ''' Standard name (and unit) is taken from the CF variables but in case a
    geophysical parameter is not in the CF standard names table it needs to be
    taken from wkv.xml (in nansat).

    Short name is taken from wkv.xml

    The table should also include the relevant GCMD science keyword
    '''
    standard_name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=50, default='')
    units = models.CharField(max_length=20)

    # The science keywords are less specific than the CF standard names -
    # therefore one science keyword can be in many parameters, whereas the
    # CF/WKV standard names are unique
    gcmd_science_keyword = models.ForeignKey(ScienceKeyword, blank=True,
            null=True, on_delete=models.CASCADE)

    objects = ParameterManager()

    def __str__(self):
        return str('%s' %self.standard_name)

    def natural_key(self):
        return (self.standard_name)

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_parameter', fields=[
                'standard_name', 'short_name', 'units', 'gcmd_science_keyword'])
        ]

from django.db import models

from nansencloud.gcmd_keywords.managers import PlatformManager
from nansencloud.gcmd_keywords.managers import InstrumentManager

# GCMD keywords loaded into the models in migrations/0001_initial.py using the
# nersc-metadata package

class Platform(models.Model):

    category = models.CharField(max_length=100)
    series_entity = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=100)

    objects = PlatformManager()

    def __str__(self):
        return self.category + ', ' + self.series_entity + ': ' + \
                self.long_name + ' (' + self.short_name + ')'

class Instrument(models.Model):

    category = models.CharField(max_length=100)
    instrument_class = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    subtype = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    long_name = models.CharField(max_length=100)

    objects = InstrumentManager()

    def __str__(self):
        return self.category + ', ' + self.instrument_class + ', ' + \
                self.type + ', ' + self.subtype + ': ' + self.long_name \
                + ' (' + self.short_name + ')'

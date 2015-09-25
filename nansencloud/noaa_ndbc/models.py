from django.contrib.gis.db import models

class StandardMeteorologicalBuoy(models.Model):
    station = models.CharField(max_length=10)
    location = models.PointField()
    year = models.IntegerField()
    opendap = models.URLField()

    objects = models.GeoManager()

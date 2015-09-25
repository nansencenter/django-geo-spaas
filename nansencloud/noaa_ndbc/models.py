from django.db import models

from nansencloud.catalog.models import Dataset

class StandardMeteorologicalBuoy(models.Model):
    dataset = models.ForeignKey(Dataset)
    station = models.CharField(max_length=10)

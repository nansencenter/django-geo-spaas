from __future__ import unicode_literals

from django.db import models

# Create your models here.
from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.processing_sar_icedrift.managers import DatasetManager

class Dataset(CatalogDataset):
    objects = DatasetManager()
    class Meta:
        proxy = True

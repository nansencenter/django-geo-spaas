from __future__ import unicode_literals

from django.db import models

# Create your models here.
from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.processing_sar_icedrift.managers import SARPairManager

class SARPair(CatalogDataset):
    objects = SARPairManager()
    class Meta:
        proxy = True

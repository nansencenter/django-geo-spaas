from django.db import models


from nansencloud.catalog.models import Dataset

from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.noaa_ndbc.managers import StandardMeteorologicalBuoyManager

class StandardMeteorologicalBuoy(CatalogDataset):
    class Meta:
        proxy = True
    objects = StandardMeteorologicalBuoyManager()

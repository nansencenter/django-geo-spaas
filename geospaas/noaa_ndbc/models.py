from django.db import models


from geospaas.catalog.models import Dataset

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.noaa_ndbc.managers import StandardMeteorologicalBuoyManager

class StandardMeteorologicalBuoy(CatalogDataset):
    class Meta:
        proxy = True
    objects = StandardMeteorologicalBuoyManager()

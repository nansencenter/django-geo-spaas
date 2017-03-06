from django.db import models


from geospaas.catalog.models import Dataset

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.ingest_lance_buoys.managers import LanceBuoyManager

class LanceBuoy(CatalogDataset):
    class Meta:
        proxy = True
    objects = LanceBuoyManager()

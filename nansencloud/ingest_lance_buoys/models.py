from django.db import models


from nansencloud.catalog.models import Dataset

from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.ingest_lance_buoys.managers import LanceBuoyManager

class LanceBuoy(CatalogDataset):
    class Meta:
        proxy = True
    objects = LanceBuoyManager()

from django.db import models


from nansencloud.catalog.models import Dataset

from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.ingest_gnssr.managers import GNSSRManager

class GNSSR(CatalogDataset):
    class Meta:
        proxy = True
    objects = GNSSRManager()

from django.db import models


from geospaas.catalog.models import Dataset

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.ingest_gnssr.managers import GNSSRManager

class GNSSR(CatalogDataset):
    class Meta:
        proxy = True
    objects = GNSSRManager()

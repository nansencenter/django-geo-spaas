from django.db import models

from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.nansat_ingestor.managers import DatasetManager

class Dataset(CatalogDataset):
    class Meta:
        proxy = True
    objects = DatasetManager()


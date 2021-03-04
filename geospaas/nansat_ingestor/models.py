from django.db import models

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.nansat_ingestor.managers import DatasetManager

class Dataset(CatalogDataset):
    class Meta:
        proxy = True
    objects = DatasetManager()


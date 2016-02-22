from django.db import models

from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import DatasetURI as CatalogDatasetURI
from nansencloud.catalog.models import Dataset as CatalogDataset

from nansencloud.ingestor.managers import DatasetURIManager
from nansencloud.ingestor.managers import DatasetManager

class Source(CatalogSource):
    class Meta:
        proxy = True

class DatasetURI(CatalogDatasetURI):
    class Meta:
        proxy = True
    objects = DatasetURIManager()

class Dataset(CatalogDataset):
    class Meta:
        proxy = True
    objects = DatasetManager()


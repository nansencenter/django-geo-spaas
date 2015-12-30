from django.db import models

from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import DatasetLocation as CatalogDatasetLocation
from nansencloud.catalog.models import Dataset as CatalogDataset

from nansencloud.ingestor.managers import DatasetLocationManager
from nansencloud.ingestor.managers import DatasetManager

class Source(CatalogSource):
    class Meta:
        proxy = True

class DatasetLocation(CatalogDatasetLocation):
    class Meta:
        proxy = True
    objects = DatasetLocationManager()

class Dataset(CatalogDataset):
    class Meta:
        proxy = True
    objects = DatasetManager()


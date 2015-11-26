from django.db import models

from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import DataLocation as CatalogDataLocation
from nansencloud.catalog.models import Dataset as CatalogDataset

from nansencloud.ingestor.managers import DataLocationManager
from nansencloud.ingestor.managers import DatasetManager

class Source(CatalogSource):
    class Meta:
        proxy = True

class DataLocation(CatalogDataLocation):
    class Meta:
        proxy = True
    objects = DataLocationManager()

class Dataset(CatalogDataset):
    class Meta:
        proxy = True
    objects = DatasetManager()


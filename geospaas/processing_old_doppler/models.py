from django.db import models

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.processing_old_doppler.managers import DatasetManager

class Dataset(CatalogDataset):

    objects = DatasetManager()

    class Meta:
        proxy = True


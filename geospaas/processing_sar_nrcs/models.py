from django.db import models

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.processing_sar_nrcs.managers import DatasetManager

class Dataset(CatalogDataset):

    objects = DatasetManager()

    class Meta:
        proxy = True


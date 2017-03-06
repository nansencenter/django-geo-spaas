from __future__ import unicode_literals

from geospaas.catalog.models import Dataset as CatalogDataset
from geospaas.processing_ascat_wind.managers import DatasetManager

class Dataset(CatalogDataset):

    objects = DatasetManager()

    class Meta:
        proxy = True


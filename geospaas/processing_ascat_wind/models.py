from __future__ import unicode_literals

from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.processing_ascat_wind.managers import DatasetManager

class Dataset(CatalogDataset):

    objects = DatasetManager()

    class Meta:
        proxy = True


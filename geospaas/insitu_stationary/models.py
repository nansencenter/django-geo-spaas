from django.db import models

from geospaas.catalog.models import Dataset as CatalogDataset

from geospaas.insitu_stationary.managers import InsituStationaryManager

class InsituStationary(CatalogDataset):
    class Meta:
        proxy = True
    objects = InsituStationaryManager()


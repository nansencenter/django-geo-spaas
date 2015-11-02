from django.db import models
from django.core.exceptions import ValidationError

from django.contrib.gis.geos import WKTReader

from nansat import Nansat

from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import DataLocation as CatalogDataLocation
from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.catalog.models import GeographicLocation

class SourceManager(models.Manager):
    def create(self, *args, **kwargs):
        ''' Create platform of a given type '''
        type = kwargs.pop('type')
        if (type, type) not in CatalogSource.SOURCE_TYPES:
            raise Exception('Wrong type %s ' % type)

        return Source(type=type, **kwargs)


class Source(CatalogSource):
    class Meta:
        proxy = True
    objects = SourceManager()


class DataLocationQuerySet(models.QuerySet):
    def new_uris(self, all_uris):
        ''' Get filenames which are not in old_filenames'''
        return sorted(list(frozenset(all_uris).difference(self.values_list(
                                                    'uri', flat=True))))


class DataLocationManager(models.Manager):
    def get_queryset(self):
        return DataLocationQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        ''' Create data location of a given protocol '''
        protocol = kwargs.pop('protocol')
        if (protocol, protocol) not in DataLocation.PROTOCOL_CHOICES:
            raise Exception('Wrong protocol %s ' % protocol)

        return DataLocation(protocol=protocol, **kwargs)


class DataLocation(CatalogDataLocation):
    class Meta:
        proxy = True
    objects = DataLocationManager()


class DatasetManager(models.Manager):
    def get_or_create(self, filename):
        ''' Create dataset and corresponding metadata '''

        # check if dataset already exists
        dataLocations = DataLocation.objects.filter(uri=filename)
        if len(dataLocations) > 0:
            return dataLocations[0].dataset, False

        # open file with Nansat
        n = Nansat(filename)
        # get metadata
        source = Source.objects.get_or_create(
                    type=n.get_metadata('source_type'),
                    platform=n.get_metadata('platform'),
                    instrument=n.get_metadata('instrument'),
                    specs=n.get_metadata().get('specs', ''))[0]

        geolocation = GeographicLocation.objects.get_or_create(
                            geometry=WKTReader().read(n.get_border_wkt()))[0]

        ds = Dataset(source=source, geolocation=geolocation,
                    time_coverage_start=n.get_metadata('time_coverage_start'),
                    time_coverage_end=n.get_metadata('time_coverage_end'))
        ds.save()

        dl = DataLocation.objects.get_or_create(protocol=DataLocation.LOCALFILE,
                                                uri=filename,
                                                dataset=ds)[0]
        return ds, True


class Dataset(CatalogDataset):
    class Meta:
        proxy = True
    objects = DatasetManager()


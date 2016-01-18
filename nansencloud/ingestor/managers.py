import json
from xml.sax.saxutils import unescape

from django.db import models
from django.contrib.gis.geos import WKTReader

from nansencloud.gcmd_keywords.models import Platform, Instrument
from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import GeographicLocation
from nansencloud.catalog.models import DataLocation, Source, Dataset

from nansat.nansat import Nansat

class DataLocationQuerySet(models.QuerySet):
    def get_non_ingested_uris(self, all_uris):
        ''' Get filenames which are not in old_filenames'''
        return sorted(list(frozenset(all_uris).difference(
                            self.values_list('uri', flat=True))))

class DataLocationManager(models.Manager):
    def get_queryset(self):
        return DataLocationQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        ''' Create data location of a given protocol '''
        protocol = kwargs.pop('protocol')
        if (protocol, protocol) not in DataLocation.PROTOCOL_CHOICES:
            raise Exception('Wrong protocol %s ' % protocol)

        return DataLocation(protocol=protocol, **kwargs)

class DatasetManager(models.Manager):
    def get_or_create(self, uri, **kwargs):
        ''' Create dataset and corresponding metadata

        Parameters:
        ----------
            uri : str
            filename openable by Nansat
        Returns:
        -------
            dataset and flag
        '''

        # check if dataset already exists
        dataLocations = DataLocation.objects.filter(uri=uri)
        if len(dataLocations) > 0:
            return dataLocations[0].dataset, False

        # open file with Nansat
        n = Nansat(uri, **kwargs)
        # get metadata
        try:
            platform = json.loads( unescape( n.get_metadata('platform'),
                {'&quot;': '"'}))
        except:
            print('ADD CORRECT METADATA IN MAPPER %s'%n.mapper)
            # TODO: add message to error instead of printing like above
            raise 
        instrument = json.loads( unescape( n.get_metadata('instrument'),
                {'&quot;': '"'}))
        source = Source.objects.get_or_create(
            platform = Platform.objects.get(
                category=platform['Category'],
                series_entity=platform['Series_Entity'],
                short_name=platform['Short_Name'],
                long_name=platform['Long_Name']
            ),
            instrument = Instrument.objects.get(
                category = instrument['Category'],
                instrument_class = instrument['Class'],
                type = instrument['Type'],
                subtype = instrument['Subtype'],
                short_name = instrument['Short_Name'],
                long_name = instrument['Long_Name']
            ),
            specs=n.get_metadata().get('specs', ''))[0]

        geolocation = GeographicLocation.objects.get_or_create(
                            geometry=WKTReader().read(n.get_border_wkt()))[0]

        ds = Dataset(source=source, geolocation=geolocation,
                    time_coverage_start=n.get_metadata('time_coverage_start'),
                    time_coverage_end=n.get_metadata('time_coverage_end'))
        ds.save()

        dl = DataLocation.objects.get_or_create(protocol=DataLocation.LOCALFILE,
                                                uri=uri,
                                                dataset=ds)[0]
        return ds, True


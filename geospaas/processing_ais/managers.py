import json
import ais.stream

from django.db import models
from django.contrib.gis.geos import WKTReader

from geospaas.vocabularies.models import Platform, Instrument
from geospaas.catalog.models import Source as CatalogSource
from geospaas.catalog.models import GeographicLocation
from geospaas.catalog.models import Dataset
from geospaas.nansat_ingestor.models import DatasetURI, Source


class DatasetManager(models.Manager):
    def create_from_file(self, uri):
        ''' Create AIS datasets and corresponding metadata from provided raw
        file

        Parameters:
        ----------
            uri : str
                path and filename 
        Returns:
        -------
            datasets and flag
        '''

        # check if data location already exists
        dataLocation = DatasetURI.objects.filter(uri=uri)
        if len(dataLocation) > 0:
            return dataLocation[0].dataset, False

        # Read file content and store it in geojson compatible dictionaries
        # Need to play a little with the different geometries - see
        # http://geojson.org/geojson-spec.html
        ships = {}
        with open(uri, 'r') as f:
            for msg in ais.stream.decode(f):
                if not ships.has_key(msg['mmsi']):
                    ships[msg['mmsi']] = {
                        'timestamps': [],
                        'points': {
                            'type': 'MultiPoint',
                            'coordinates': [],
                        }
                    }
                try:
                    ships[msg['mmsi']]['timestamps'].append(
                        msg['tagblock_timestamp'])
                    ships[msg['mmsi']]['points']['coordinates'].append(
                        [msg['x'], msg['y']])
                    #'true_heading': msg['true_heading'],
                except KeyError:
                    continue

        import ipdb
        ipdb.set_trace()
        print 'hei'


        ## get metadata
        #try:
        #    platform = json.loads(n.get_metadata('platform'))
        #except:
        #    print('ADD CORRECT METADATA IN MAPPER %s'%n.mapper)
        #    # TODO: add message to error instead of printing like above
        #    raise 
        #instrument = json.loads(n.get_metadata('instrument'))
        #source = Source.objects.get_or_create(
        #    platform = Platform.objects.get(
        #        category=platform['Category'],
        #        series_entity=platform['Series_Entity'],
        #        short_name=platform['Short_Name'],
        #        long_name=platform['Long_Name']
        #    ),
        #    instrument = Instrument.objects.get(
        #        category = instrument['Category'],
        #        instrument_class = instrument['Class'],
        #        type = instrument['Type'],
        #        subtype = instrument['Subtype'],
        #        short_name = instrument['Short_Name'],
        #        long_name = instrument['Long_Name']
        #    ),
        #    specs=n.get_metadata().get('specs', ''))[0]

        #geolocation = GeographicLocation.objects.get_or_create(
        #                    geometry=WKTReader().read(n.get_border_wkt()))[0]

        #ds = Dataset(source=source, geolocation=geolocation,
        #            time_coverage_start=n.get_metadata('time_coverage_start'),
        #            time_coverage_end=n.get_metadata('time_coverage_end'))
        #ds.save()

        #dl = DatasetURI.objects.get_or_create(
        #                                        uri=uri,
        #                                        dataset=ds)[0]
        #return ds, True


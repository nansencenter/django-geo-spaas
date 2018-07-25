import uuid
import warnings
import json
from xml.sax.saxutils import unescape

from nansat.nansat import Nansat

from django.db import models
from django.contrib.gis.geos import WKTReader

from geospaas.utils import validate_uri, nansat_filename
from geospaas.vocabularies.models import Platform
from geospaas.vocabularies.models import Instrument
from geospaas.vocabularies.models import DataCenter
from geospaas.vocabularies.models import ISOTopicCategory
from geospaas.catalog.models import GeographicLocation
from geospaas.catalog.models import DatasetURI, Source, Dataset

class DatasetManager(models.Manager):
    optional_fields = {
        'entry_id'           : {'nansat_key': 'Entry ID',           'default': uuid.uuid4},
        'entry_title'        : {'nansat_key': 'Entry Title',        'default': lambda : 'NONE'},
        'data_center'        : {'nansat_key': 'Data Center',
                                'default': lambda : DataCenter.objects.get(short_name='NERSC')},
        'summary'            : {'nansat_key': 'Summary',            'default': lambda : 'NONE'},
        'ISO_topic_category' : {'nansat_key': 'ISO Topic Category',
                                'default': lambda : ISOTopicCategory.objects.get(name='Oceans')},
    }

    def get_or_create(self, uri, *args, **kwargs):
        ''' Create dataset and corresponding metadata

        Parameters:
        ----------
            uri : str
                  URI to file or stream openable by Nansat
        Returns:
        -------
            dataset and flag
        '''

        # Validate uri - this should fail if the uri doesn't point to a valid
        # file or stream
        valid_uri = validate_uri(uri)

        # check if dataset already exists
        uris = DatasetURI.objects.filter(uri=uri)
        if len(uris) > 0:
            return uris[0].dataset, False

        n = Nansat(nansat_filename(uri), **kwargs)

        # get metadata
        platform = json.loads( unescape( n.get_metadata('platform'),
                {'&quot;': '"'}))
        instrument = json.loads( unescape( n.get_metadata('instrument'),
                {'&quot;': '"'}))
        pp = Platform.objects.get(
                category=platform['Category'],
                series_entity=platform['Series_Entity'],
                short_name=platform['Short_Name'],
                long_name=platform['Long_Name']
            )
        ii = Instrument.objects.get(
                category = instrument['Category'],
                instrument_class = instrument['Class'],
                type = instrument['Type'],
                subtype = instrument['Subtype'],
                short_name = instrument['Short_Name'],
                long_name = instrument['Long_Name']
            )
        specs = n.get_metadata().get('specs', '')
        source = Source.objects.get_or_create(
            platform = pp,
            instrument = ii,
            specs=specs)[0]

        # Find coverage to set number of points in the geolocation
        geolocation = GeographicLocation.objects.get_or_create(
                      geometry=WKTReader().read(n.get_border_wkt()))[0]

        # get metadata for optional fields or take from self.optional_fields
        metadata = n.get_metadata()
        kwargs = {}
        for field in self.optional_fields:
            nansat_key = self.optional_fields[field]['nansat_key']
            default_val = self.optional_fields[field]['default']()
            kwargs[field] = metadata.get(nansat_key, default_val)
            if nansat_key not in metadata:
                warnings.warn('''
                    %s is hardcoded to "%s" - this should
                    be provided in the nansat metadata instead..
                    '''%(nansat_key, default_val))

        ds = Dataset(
                time_coverage_start=n.get_metadata('time_coverage_start'),
                time_coverage_end=n.get_metadata('time_coverage_end'),
                source=source,
                geographic_location=geolocation,
                **kwargs)
        ds.save()

        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

        return ds, True


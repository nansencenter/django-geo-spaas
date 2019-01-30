import uuid
import warnings
import json
from xml.sax.saxutils import unescape

import pythesint as pti

from nansat.nansat import Nansat

from django.db import models
from django.contrib.gis.geos import WKTReader

from geospaas.utils import validate_uri, nansat_filename
from geospaas.vocabularies.models import (Platform,
                                          Instrument,
                                          DataCenter,
                                          ISOTopicCategory,
                                          Location)
from geospaas.catalog.models import GeographicLocation, DatasetURI, Source, Dataset

class DatasetManager(models.Manager):
    default_char_fields = {
        'entry_id'           : lambda : 'NERSC_' + str(uuid.uuid4()),
        'entry_title'        : lambda : 'NONE',
        'summary'            : lambda : 'NONE',
    }

    default_foreign_keys = {
        'gcmd_location'      : {'model': Location,
                                'value': pti.get_gcmd_location('SEA SURFACE')},
        'data_center'        : {'model': DataCenter,
                                'value': pti.get_gcmd_provider('NERSC')},
        'ISO_topic_category' : {'model': ISOTopicCategory,
                                'value': pti.get_iso19115_topic_category('Oceans')},
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

        # Open file with Nansat
        n = Nansat(nansat_filename(uri), **kwargs)

        # get metadata from Nansat and get objects from vocabularies
        n_metadata = n.get_metadata()

        # set compulsory metadata (source)
        platform, _ = Platform.objects.get_or_create(json.loads(n_metadata['platform']))
        instrument, _ = Instrument.objects.get_or_create(json.loads(n_metadata['instrument']))
        specs = n_metadata.get('specs', '')
        source, _ = Source.objects.get_or_create(platform=platform,
                                                 instrument=instrument,
                                                 specs=specs)

        # set optional CharField metadata from Nansat or from self.default_char_fields
        options = {}
        for name in self.default_char_fields:
            if name not in n_metadata:
                warnings.warn('%s is not provided in Nansat metadata!' % name)
                options[name] = self.default_char_fields[name]()
            else:
                options[name] = n_metadata[name]

        # set optional ForeignKey metadata from Nansat or from self.default_foreign_keys
        for name in self.default_foreign_keys:
            value = self.default_foreign_keys[name]['value']
            model = self.default_foreign_keys[name]['model']
            if name not in n_metadata:
                warnings.warn('%s is not provided in Nansat metadata!' % name)
            else:
                try:
                    value = json.loads(n_metadata[name])
                except:
                    warnings.warn('%s value of %s  metadata provided in Nansat is wrong!' %
                                    (n_metadata[name], name))
            options[name], _ = model.objects.get_or_create(value)

        # Find coverage to set number of points in the geolocation
        if len(n.vrt.dataset.GetGCPs()) > 0:
            n.reproject_gcps()
        geolocation = GeographicLocation.objects.get_or_create(
                      geometry=WKTReader().read(n.get_border_wkt()))[0]

        # create parameter
        from geospaas.vocabularies.models import Parameter
        nansat_bands = n.bands()
        for band_number in range(1, len(nansat_bands)+1):
            band_dict = nansat_bands[band_number]
            if 'standard_name' in band_dict.keys():
                parameter = Parameter.objects.get_or_create(nansat_bands[band_number])[0]





        # create dataset
        ds = Dataset(
                time_coverage_start=n.get_metadata('time_coverage_start'),
                time_coverage_end=n.get_metadata('time_coverage_end'),
                source=source,
                geographic_location=geolocation,
                **options)
        ds.save()
        # create dataset URI
        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

        return ds, True


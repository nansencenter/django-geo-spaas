import uuid
import warnings
import json
from xml.sax.saxutils import unescape

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import pythesint as pti

from nansat.nansat import Nansat

from django.db import models
from django.contrib.gis.geos import WKTReader

from geospaas.utils.utils import validate_uri, nansat_filename
from geospaas.vocabularies.models import (Platform,
                                          Instrument,
                                          DataCenter,
                                          ISOTopicCategory,
                                          Location)
from geospaas.catalog.models import GeographicLocation, DatasetURI, Source, Dataset
from geospaas.catalog.managers import DAP_SERVICE_NAME, OPENDAP_SERVICE 
from geospaas.catalog.managers import FILE_SERVICE_NAME, LOCAL_FILE_SERVICE 

class DatasetManager(models.Manager):

    def get_or_create(self, uri, n_points=10, uri_filter_args=None, *args, **kwargs):
        """ Create dataset and corresponding metadata

        Parameters:
        ----------
            uri : str
                  URI to file or stream openable by Nansat
            n_points : int
                  Number of border points (default is 10)
            uri_filter_args : dict
                Extra DatasetURI filter arguments if several datasets can refer to the same URI

        Returns:
        -------
            dataset and flag
        """
        if not uri_filter_args:
            uri_filter_args = {}

        # Validate uri - this should raise an exception if the uri doesn't point to a valid
        # file or stream
        validate_uri(uri)

        # Several datasets can refer to the same uri (e.g., scatterometers and svp drifters), so we
        # need to pass uri_filter_args
        uris = DatasetURI.objects.filter(uri=uri, **uri_filter_args)
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

        default_char_fields = {
            'entry_id'           : lambda : 'NERSC_' + str(uuid.uuid4()),
            'entry_title'        : lambda : 'NONE',
            'summary'            : lambda : 'NONE',
        }

        # set optional CharField metadata from Nansat or from default_char_fields
        options = {}
        for name in default_char_fields:
            if name not in n_metadata:
                warnings.warn('%s is not provided in Nansat metadata!' % name)
                options[name] = default_char_fields[name]()
            else:
                options[name] = n_metadata[name]

        default_foreign_keys = {
            'gcmd_location'      : {'model': Location,
                                    'value': pti.get_gcmd_location('SEA SURFACE')},
            'data_center'        : {'model': DataCenter,
                                    'value': pti.get_gcmd_provider('NERSC')},
            'ISO_topic_category' : {'model': ISOTopicCategory,
                                    'value': pti.get_iso19115_topic_category('Oceans')},
        }

        # set optional ForeignKey metadata from Nansat or from default_foreign_keys
        for name in default_foreign_keys:
            value = default_foreign_keys[name]['value']
            model = default_foreign_keys[name]['model']
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
                      geometry=WKTReader().read(n.get_border_wkt(nPoints=n_points)))[0]


        # create dataset
        ds, created = Dataset.objects.get_or_create(
                time_coverage_start=n.get_metadata('time_coverage_start'),
                time_coverage_end=n.get_metadata('time_coverage_end'),
                source=source,
                geographic_location=geolocation,
                **options)

        uri_scheme = urlparse(uri).scheme
        if 'http' in uri_scheme:
            service_name = DAP_SERVICE_NAME
            service = OPENDAP_SERVICE
        else: 
            service_name = FILE_SERVICE_NAME
            service = LOCAL_FILE_SERVICE
        # create dataset URI
        ds_uri, _ = DatasetURI.objects.get_or_create(name=service_name, service=service, uri=uri,
                dataset=ds)

        return ds, created


import json
import uuid
import warnings

import pythesint as pti
from django.contrib.gis.geos import WKTReader
from django.db import models

from geospaas.catalog.managers import FILE_SERVICE_NAME, LOCAL_FILE_SERVICE
from geospaas.catalog.models import (Dataset, DatasetURI,
                                     GeographicLocation, Source)
from geospaas.utils.utils import nansat_filename, validate_uri
from geospaas.vocabularies.models import (DataCenter, Instrument,
                                          ISOTopicCategory, Location,
                                          Parameter, Platform)
from nansat.nansat import Nansat


class DatasetManager(models.Manager):

    def get_or_create(self,
                      uri,
                      n_points=10,
                      uri_filter_args=None,
                      uri_service_name=FILE_SERVICE_NAME,
                      uri_service_type=LOCAL_FILE_SERVICE,
                      *args, **kwargs):
        """ Create dataset and corresponding metadata

        Parameters:
        ----------
            uri : str
                  URI to file or stream openable by Nansat
            n_points : int
                  Number of border points (default is 10)
            uri_filter_args : dict
                Extra DatasetURI filter arguments if several datasets can refer to the same URI
            uri_service_name : str
                name of the service which is used  ('dapService', 'fileService', 'http' or 'wms')
            uri_service_type : str
                type of the service which is used  ('OPENDAP', 'local', 'HTTPServer' or 'WMS')

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

        entry_id = n_metadata.get('entry_id', None)
        # set compulsory metadata (source)
        platform, _ = Platform.objects.get_or_create(
            json.loads(n_metadata['platform']))
        instrument, _ = Instrument.objects.get_or_create(
            json.loads(n_metadata['instrument']))
        specs = n_metadata.get('specs', '')
        source, _ = Source.objects.get_or_create(platform=platform,
                                                 instrument=instrument,
                                                 specs=specs)

        default_char_fields = {
            # Adding NERSC_ in front of the id violates the string representation of the uuid
            #'entry_id': lambda: 'NERSC_' + str(uuid.uuid4()),
            'entry_id': lambda: str(uuid.uuid4()),
            'entry_title': lambda: 'NONE',
            'summary': lambda: 'NONE',
        }

        # set optional CharField metadata from Nansat or from default_char_fields
        options = {}
        try:
            existing_ds = Dataset.objects.get(entry_id=entry_id)
        except Dataset.DoesNotExist:
            existing_ds = None
        for name in default_char_fields:
            if name not in n_metadata:
                warnings.warn('%s is not provided in Nansat metadata!' % name)
                # prevent overwriting of existing values by defaults
                if existing_ds:
                    options[name] = existing_ds.__getattribute__(name)
                else:
                    options[name] = default_char_fields[name]()
            else:
                options[name] = n_metadata[name]

        default_foreign_keys = {
            'gcmd_location': {'model': Location,
                              'value': pti.get_gcmd_location('SEA SURFACE')},
            'data_center': {'model': DataCenter,
                            'value': pti.get_gcmd_provider('NERSC')},
            'ISO_topic_category': {'model': ISOTopicCategory,
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
            if existing_ds:
                options[name] = existing_ds.__getattribute__(name)
            else:
                options[name], _ = model.objects.get_or_create(value)

        # Find coverage to set number of points in the geolocation
        if len(n.vrt.dataset.GetGCPs()) > 0:
            n.reproject_gcps()
        geolocation = GeographicLocation.objects.get_or_create(
            geometry=WKTReader().read(n.get_border_wkt(nPoints=n_points)))[0]

        # create dataset
        # - the get_or_create method should use get_or_create here as well,
        #   or its name should be changed - see issue #127
        ds, created = Dataset.objects.update_or_create(entry_id=options['entry_id'], defaults={
            'time_coverage_start': n.get_metadata('time_coverage_start'),
            'time_coverage_end': n.get_metadata('time_coverage_end'),
            'source': source,
            'geographic_location': geolocation,
            'gcmd_location': options["gcmd_location"],
            'ISO_topic_category': options["ISO_topic_category"],
            "data_center": options["data_center"],
            'entry_title': options["entry_title"],
            'summary': options["summary"]}
        )

        # create parameter
        all_band_meta = n.bands()
        for band_id in range(1, len(all_band_meta)+1):
            band_meta = all_band_meta[band_id]
            standard_name = band_meta.get('standard_name', None)
            short_name = band_meta.get('short_name', None)
            units = band_meta.get('units', None)
            if standard_name in ['latitude', 'longitude', None]:
                continue
            params = Parameter.objects.filter(standard_name=standard_name)
            if params.count() > 1 and short_name is not None:
                params = params.filter(short_name=short_name)
            if params.count() > 1 and units is not None:
                params = params.filter(units=units)
            if params.count() >= 1:
                ds.parameters.add(params[0])

        # create dataset URI
        DatasetURI.objects.get_or_create(
            name=uri_service_name,
            service=uri_service_type,
            uri=uri,
            dataset=ds)

        return ds, created

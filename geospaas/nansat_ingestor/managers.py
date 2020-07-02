import json
import uuid
import warnings
from xml.sax.saxutils import unescape

import pythesint as pti
from django.contrib.gis.geos import WKTReader
from django.db import models
from nansat.nansat import Nansat

from geospaas.catalog.managers import (DAP_SERVICE_NAME, FILE_SERVICE_NAME,
                                       LOCAL_FILE_SERVICE, OPENDAP_SERVICE)
from geospaas.catalog.models import (Dataset, DatasetParameter, DatasetURI,
                                     GeographicLocation, Source)
from geospaas.utils.utils import nansat_filename, validate_uri
from geospaas.vocabularies.models import (DataCenter, Instrument,
                                          ISOTopicCategory, Location,
                                          Parameter, Platform)
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


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
        entry_id = n_metadata['entry_id']
        if Dataset.objects.filter(entry_id__icontains=entry_id).count() >= 1:
            qds = Dataset.objects.get(
                entry_id__icontains=entry_id)  # query of found dataset
            assert len(qds) == 1
            ds = qds.first()  # this dataset (which is the first and the only one) must be updated
            # ds. Here is the place for setting the metadata from the nansat that comes from the localfile

            platform, _ = Platform.objects.get_or_create(
                json.loads(n_metadata['platform']))
            instrument, _ = Instrument.objects.get_or_create(
                json.loads(n_metadata['instrument']))
            specs = n_metadata.get('specs', '')
            source, _ = Source.objects.get_or_create(platform=platform,
                                                     instrument=instrument,
                                                     specs=specs)
            ds.source = source  # update source

            if 'entry_title' in n_metadata and n_metadata['entry_title'] is not None:
                # update entry_title
                ds.entry_title = n_metadata['entry_title']
            if 'summary' in n_metadata and n_metadata['summary'] is not None:
                ds.summary = n_metadata['summary']  # update summary
            if 'time_coverage_start' in n_metadata and n_metadata['time_coverage_start'] is not None:
                # update time_coverage_start
                ds.time_coverage_start = n_metadata['time_coverage_start']
            if 'time_coverage_end' in n_metadata and n_metadata['time_coverage_end'] is not None:
                # update time_coverage_end
                ds.time_coverage_end = n_metadata['time_coverage_end']

            if len(n.vrt.dataset.GetGCPs()) > 0:
                n.reproject_gcps()
            geolocation = GeographicLocation.objects.get_or_create(
                geometry=WKTReader().read(n.get_border_wkt(nPoints=n_points)))[0]
            ds.geographic_location = geolocation

            if 'data_center' in n_metadata and n_metadata['data_center'] is not None:
                ds.data_center = DataCenter.objects.get_or_create(
                    json.loads(n_metadata['data_center']))[0]
            if 'gcmd_location' in n_metadata and n_metadata['gcmd_location'] is not None:
                ds.gcmd_location = Location.objects.get_or_create(
                    json.loads(n_metadata['gcmd_location']))[0]
            if 'iso_topic_category' in n_metadata and n_metadata['iso_topic_category'] is not None:
                ds.ISO_topic_category = ISOTopicCategory.objects.get_or_create(
                    json.loads(n_metadata['iso_topic_category']))[0]
            created = False
            warnings.warn('Dataset with entry_id %s has been updated!' %
                          (n_metadata['entry_id']))
        else:
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
                'entry_id': lambda: 'NERSC_' + str(uuid.uuid4()),
                'entry_title': lambda: 'NONE',
                'summary': lambda: 'NONE',
            }

            # set optional CharField metadata from Nansat or from default_char_fields
            options = {}
            for name in default_char_fields:
                if name not in n_metadata:
                    warnings.warn(
                        '%s is not provided in Nansat metadata!' % name)
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
                    warnings.warn(
                        '%s is not provided in Nansat metadata!' % name)
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
                dsp, dsp_created = DatasetParameter.objects.get_or_create(
                    dataset=ds, parameter=params[0])
                ds.parameters.add(params[0])

        # create dataset URI
        ds_uri, _ = DatasetURI.objects.get_or_create(
            name=uri_service_name,
            service=uri_service_type,
            uri=uri,
            dataset=ds)

        return ds, created

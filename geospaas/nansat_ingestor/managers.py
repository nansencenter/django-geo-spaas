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
    optional_fields = {
        'entry_id'           : {'nansat_key': 'entry_id',     'default': uuid.uuid4},
        'entry_title'        : {'nansat_key': 'entry_title',  'default': lambda : 'NONE'},
        'summary'            : {'nansat_key': 'summary',      'default': lambda : 'NONE'},
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

        platform = json.loads(n_metadata['platform'])
        platform = Platform.objects.get(
                category=platform['Category'],
                series_entity=platform['Series_Entity'],
                short_name=platform['Short_Name'],
                long_name=platform['Long_Name'])

        instrument = json.loads(n_metadata['instrument'])
        instrument = Instrument.objects.get(
                category = instrument['Category'],
                instrument_class = instrument['Class'],
                type = instrument['Type'],
                subtype = instrument['Subtype'],
                short_name = instrument['Short_Name'],
                long_name = instrument['Long_Name'])

        specs = n_metadata.get('specs', '')
        source, _ = Source.objects.get_or_create(platform=platform,
                                                 instrument=instrument,
                                                 specs=specs)

        data_center = json.loads(n_metadata['data_center'])
        data_center = DataCenter.objects.get(
                bucket_level0=data_center['Bucket_Level0'],
                bucket_level1=data_center['Bucket_Level1'],
                bucket_level2=data_center['Bucket_Level2'],
                bucket_level3=data_center['Bucket_Level3'],
                short_name=data_center['Short_Name'],
                long_name=data_center['Long_Name'],
                data_center_url=data_center['Data_Center_URL'])

        iso_topic_category = json.loads(n_metadata['iso_topic_category'])
        iso_topic_category = ISOTopicCategory.objects.get(name=iso_topic_category['iso_topic_category'])

        if 'gcmd_location' in n_metadata:
            gcmd_location = json.loads(n_metadata['gcmd_location'])
        else:
            gcmd_location = pti.get_gcmd_location('SEA SURFACE')
        gcmd_location = Location.objects.get(
                        category=gcmd_location['Location_Category'],
                        type=gcmd_location['Location_Type'],
                        subregion1=gcmd_location['Location_Subregion1'],
                        subregion2=gcmd_location['Location_Subregion2'],
                        subregion3=gcmd_location['Location_Subregion3'])

        # Find coverage to set number of points in the geolocation
        if len(n.vrt.dataset.GetGCPs()) > 0:
            n.reproject_gcps()
        geolocation = GeographicLocation.objects.get_or_create(
                      geometry=WKTReader().read(n.get_border_wkt()))[0]

        # get optional metadata from Nansat or from self.optional_fields
        kwargs = {}
        for field in self.optional_fields:
            nansat_key = self.optional_fields[field]['nansat_key']
            default_val = self.optional_fields[field]['default']()
            kwargs[field] = n_metadata.get(nansat_key, default_val)
            if nansat_key not in n_metadata:
                warnings.warn('''
                    %s is hardcoded to "%s" - this should
                    be provided in the nansat metadata instead..
                    '''%(nansat_key, default_val))

        # create dataset
        ds = Dataset(
                time_coverage_start=n.get_metadata('time_coverage_start'),
                time_coverage_end=n.get_metadata('time_coverage_end'),
                source=source,
                geographic_location=geolocation,
                data_center=data_center,
                ISO_topic_category=iso_topic_category,
                gcmd_location=gcmd_location,
                **kwargs)
        ds.save()
        # create dataset URI
        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

        return ds, True


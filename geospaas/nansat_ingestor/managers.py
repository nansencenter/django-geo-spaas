import warnings
import json
from xml.sax.saxutils import unescape

import pythesint as pti

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
        # if not specs:
        #     specs = n.get_metadata().get('Entry Title', '')
        source = Source.objects.get_or_create(
            platform = pp,
            instrument = ii,
            specs=specs)[0]

        # Find coverage to set number of points in the geolocation
        geolocation = GeographicLocation.objects.get_or_create(
                      geometry=WKTReader().read(n.get_border_wkt()))[0]
        try:
            entrytitle = n.get_metadata('Entry Title')
        except:
            entrytitle = 'NONE'
            warnings.warn('''
                Entry title is hardcoded to "NONE" - this should
                be provided in the nansat metadata instead..
                ''')
        try:
            sname = n.get_metadata('Data Center')['Short_Name']
        except:
            sname = pti.get_gcmd_provider('nersc')['Short_Name']
            warnings.warn('''
                Data center is hardcoded to "NERSC" - this should
                be provided in the nansat metadata instead..
                ''')
        dc = DataCenter.objects.get(short_name=sname)
        try:
            isocatname = n.get_metadata('ISO Topic Category')
        except:
            isocatname = pti.get_iso19115_topic_category('oceans')['iso_topic_category']
            warnings.warn('''
                ISO topic category is hardcoded to "Oceans" - this should
                be provided in the nansat metadata instead..
                ''')
        iso_category = ISOTopicCategory.objects.get(name=isocatname)
        try:
            summary = n.get_metadata('Summary')
        except:
            summary = 'NONE'
            warnings.warn('''
                Summary is hardcoded to "NONE" - this should
                be provided in the nansat metadata instead..
                ''')
        try:
            gcmd_location = GCMDLocation.objects.get(type =
                    n.get_metadata('gcmd_location')['Location_Type'])
        except:
            gcmd_location = GCMDLocation.objects.get(type = 
                    pti.get_gcmd_location('sea surface')['Location_Type'])
            warnings.warn('''
                GCMD location is hardcoded to "Sea surface" - this should
                be provided in the nansat metadata instead..
                ''')

        ds = Dataset(
                entry_title=entrytitle,
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = summary,
                time_coverage_start=n.get_metadata('time_coverage_start'),
                time_coverage_end=n.get_metadata('time_coverage_end'),
                source=source,
                gcmd_location = gcmd_location,
                geographic_location=geolocation)
        ds.save()

        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

        return ds, True


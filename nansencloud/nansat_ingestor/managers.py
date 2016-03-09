import warnings
import json, urllib2
from urlparse import urlparse
from xml.sax.saxutils import unescape

from nansat.nansat import Nansat

from django.db import models
from django.contrib.gis.geos import WKTReader

from nansencloud.vocabularies.models import Platform
from nansencloud.vocabularies.models import Instrument
from nansencloud.vocabularies.models import DataCenter
from nansencloud.vocabularies.models import ISOTopicCategory
from nansencloud.catalog.models import GeographicLocation
from nansencloud.catalog.models import DatasetURI, Source, Dataset

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

        # Validate uri - this should fail if the data isn't available
        request = urllib2.Request(uri)
        response = urllib2.urlopen(request)
        response.close()
        uri_content = urlparse(uri)

        # check if dataset already exists
        uris = DatasetURI.objects.filter(uri=uri)
        if len(uris) > 0:
            return uris[0].dataset, False

        # Check if data should be read as stream or as file? Or just:
        # open with Nansat
        if uri_content.scheme=='file':
            n = Nansat(uri_content.path)
        elif uri_content.scheme=='ftp':
            n = Nansat(urllib.urlretrieve(uri)[0])
        else:
            n = Nansat(uri)
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
        source = Source.objects.get_or_create(
            platform = pp,
            instrument = ii,
            specs=n.get_metadata().get('specs', ''))[0]

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
            sname = n.get_metadata('Data Center')
        except:
            sname = 'NERSC'
            warnings.warn('''
                Data center is hardcoded to "NERSC" - this should 
                be provided in the nansat metadata instead..
                ''')
        dc = DataCenter.objects.get(short_name=sname)
        try:
            isocatname = n.get_metadata('ISO Topic Category')
        except:
            isocatname = 'Oceans'
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
        ds = Dataset(
                entry_title=entrytitle, 
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = summary,
                time_coverage_start=n.get_metadata('time_coverage_start'),
                time_coverage_end=n.get_metadata('time_coverage_end'),
                source=source,
                geographic_location=geolocation)
        ds.save()

        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

        return ds, True


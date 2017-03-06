#-------------------------------------------------------------------------------
# Name:     managers.py
# Purpose:
#
# Author:       Morten Wergeland Hansen
# Modified: Morten Wergeland Hansen
#
# Created:  21.01.2015
# Last modified:21.01.2015 19:34
# Copyright:    (c) NERSC
# License:
#-------------------------------------------------------------------------------
import numpy as np
import datetime
import netCDF4

import pythesint as pti

from django.db import models
from django.contrib.gis.geos import GEOSGeometry

from geospaas.utils import validate_uri, nansat_filename

from geospaas.vocabularies.models import Platform
from geospaas.vocabularies.models import Instrument
from geospaas.vocabularies.models import DataCenter
from geospaas.vocabularies.models import ISOTopicCategory
from geospaas.catalog.models import GeographicLocation
from geospaas.catalog.models import DatasetURI, Source, Dataset

# test url
# uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2014.nc'
# uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2012.nc'
class StandardMeteorologicalBuoyManager(models.Manager):

    def get_or_create(self, uri, *args, **kwargs):
        ''' Create dataset and corresponding metadata

        Parameters:
        ----------
            uri : str
                  URI to file or stream openable by netCDF4.Dataset
        Returns:
        -------
            dataset and flag
        '''
        # check if dataset already exists
        uris = DatasetURI.objects.filter(uri=uri)
        if len(uris) > 0:
            return uris[0].dataset, False

        # set source
        platform = pti.get_gcmd_platform('BUOYS')
        instrument = pti.get_gcmd_instrument('WIND MONITOR')

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
            instrument = ii)[0]

        nc_dataset = netCDF4.Dataset(uri)

        station_name = nc_dataset.station
        longitude = nc_dataset.variables['longitude'][0]
        latitude = nc_dataset.variables['latitude'][0]
        location = GEOSGeometry('POINT(%s %s)' % (longitude, latitude))

        geolocation = GeographicLocation.objects.get_or_create(
                            geometry=location)[0]

        entrytitle = nc_dataset.comment
        dc = DataCenter.objects.get(short_name='DOC/NOAA/NWS/NDBC')
        iso_category = ISOTopicCategory.objects.get(name='Oceans')
        summary = 'NONE'

        t0 = datetime.datetime(1970,1,1) + datetime.timedelta(seconds=int(nc_dataset.variables['time'][0]))
        t1 = datetime.datetime(1970,1,1) + datetime.timedelta(seconds=int(nc_dataset.variables['time'][-1]))

        ds = Dataset(
                entry_title=entrytitle,
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = summary,
                time_coverage_start=t0,
                time_coverage_end=t1,
                source=source,
                geographic_location=geolocation)
        ds.save()

        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]


        return ds, True


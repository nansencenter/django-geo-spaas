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
from dateutil.parser import parse

import pythesint as pti

from django.db import models
from django.contrib.gis.geos import LineString

from nansencloud.utils import validate_uri, nansat_filename

from nansencloud.vocabularies.models import Platform
from nansencloud.vocabularies.models import Instrument
from nansencloud.vocabularies.models import DataCenter
from nansencloud.vocabularies.models import ISOTopicCategory
from nansencloud.catalog.models import GeographicLocation
from nansencloud.catalog.models import DatasetURI, Source, Dataset

def get_dates_lon_lat(fname):
    ''' Get valid dates, lon and lat arrays from file'''
    data = np.recfromcsv(fname, invalid_raise=False, delimiter=',',names=True)
    gpi = data['lat'] > 0
    valid_dates = data['date'][gpi]
    valid_lon = data['lon'][gpi]
    valid_lat = data['lat'][gpi]

    return valid_dates, valid_lon, valid_lat

def get_lon_lat(fname, start_date, end_date):
    ''' Get valid lon,lat for given time period '''
    data = np.recfromcsv(fname, invalid_raise=False, delimiter=',',names=True)
    dates = np.array([np.datetime64(date) for date in data['date']])
    gpi = (data['lat'] > 0) * (dates >= start_date) * (dates < end_date)
    valid_lon = data['lon'][gpi]
    valid_lat = data['lat'][gpi]

    return valid_lon, valid_lat

# test url
# uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2014.nc'
# uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2012.nc'
class LanceBuoyManager(models.Manager):
    def add_buoy_data_from_file(self, uri, period_days=1):
        ''' Create all datasets from given file and add corresponding metadata

        Parameters:
        ----------
            uri : str
                  URI to file or stream openable by netCDF4.Dataset
        Returns:
        -------
            dataset and flag
        '''
        # set metadata
        pp = Platform.objects.get(short_name='BUOYS')
        ii = Instrument.objects.get(short_name = 'DRIFTING BUOYS')
        src = Source.objects.get_or_create(platform = pp, instrument = ii)[0]
        dc = DataCenter.objects.get(short_name = 'NO/NPI')
        iso = ISOTopicCategory.objects.get(name='Oceans')

        # read dates, lon, lat from file
        dates, lon, lat = get_dates_lon_lat(uri)
        dates0 = parse(dates[0])
        dates1 = parse(dates[-1])

        # add all 1-day chunks to database
        date = datetime.datetime(dates0.year, dates0.month, dates0.day)
        cnt = 0
        while date < dates1:
            start_date = date
            end_date = start_date + datetime.timedelta(period_days)
            lon, lat = get_lon_lat(uri, start_date, end_date)
            self.add_trajectory(uri, start_date, end_date, lon, lat, src, dc, iso)
            date = end_date
            cnt += 1

        return cnt

    def add_trajectory(self, uri, start_date, end_date, lon, lat, src, dc, iso):
        ''' Add one chunk of trajectory to database '''
        line1 = LineString((zip(lon, lat)))
        geolocation = GeographicLocation.objects.get_or_create(geometry=line1)[0]

        ds = Dataset.objects.get_or_create(
                    entry_title=uri + start_date.strftime('_%Y-%m-%d'),
                    ISO_topic_category = iso,
                    data_center = dc,
                    summary = uri,
                    time_coverage_start=start_date,
                    time_coverage_end=end_date,
                    source=src,
                    geographic_location=geolocation)[0]

        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

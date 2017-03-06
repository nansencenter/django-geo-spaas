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
from xml.dom import minidom

import pythesint as pti

from django.db import models
from django.contrib.gis.geos import LineString

from geospaas.utils import validate_uri, nansat_filename

from geospaas.vocabularies.models import Platform
from geospaas.vocabularies.models import Instrument
from geospaas.vocabularies.models import DataCenter
from geospaas.vocabularies.models import ISOTopicCategory
from geospaas.catalog.models import GeographicLocation
from geospaas.catalog.models import DatasetURI, Source, Dataset

# http://www.johndcook.com/blog/2009/07/21/ieee-arithmetic-python/
def isnan(x): return type(x) is float and x != x

def get_dates_lon_lat(fname):
    ''' Get valid dates, lon and lat arrays from file'''
    xmldoc = minidom.parse(fname)
    items  = xmldoc.getElementsByTagName('L2DataPerEpoch')
    valid_dates = []
    valid_lon   = []
    valid_lat   = []

    for item in items:
        spd = float(item.getElementsByTagName("WindSpeed")[              0].childNodes[0].nodeValue)
        mss = float(item.getElementsByTagName("MSS")[                    0].childNodes[0].nodeValue)
        dat =       item.getElementsByTagName("IntegrationMidPointTime")[0].childNodes[0].nodeValue
        lat = float(item.getElementsByTagName("double")[                 0].childNodes[0].nodeValue)
        lon = float(item.getElementsByTagName("double")[                 1].childNodes[0].nodeValue)
        hgt = float(item.getElementsByTagName("double")[                 2].childNodes[0].nodeValue)
        if not isnan(spd) and not isnan(mss) and lat > -99.0:
            valid_dates.append(dat)
            valid_lon.append(  lon)
            valid_lat.append(  lat)

    return valid_dates, valid_lon, valid_lat

def get_lon_lat(fname, start_date, end_date):
    ''' Get valid lon,lat for given time period '''
    xmldoc = minidom.parse(fname)
    items  = xmldoc.getElementsByTagName('L2DataPerEpoch')
    valid_lon = []
    valid_lat = []

    beg = np.datetime64(start_date)
    end = np.datetime64(end_date)
    for item in items:
        spd =         float(item.getElementsByTagName("WindSpeed")[              0].childNodes[0].nodeValue)
        mss =         float(item.getElementsByTagName("MSS")[                    0].childNodes[0].nodeValue)
        dat = np.datetime64(item.getElementsByTagName("IntegrationMidPointTime")[0].childNodes[0].nodeValue)
        lat =         float(item.getElementsByTagName("double")[                 0].childNodes[0].nodeValue)
        lon =         float(item.getElementsByTagName("double")[                 1].childNodes[0].nodeValue)
        hgt =         float(item.getElementsByTagName("double")[                 2].childNodes[0].nodeValue)
        if not isnan(spd) and not isnan(mss) and dat >= beg and dat < end and lat > -99.0:
            valid_lon.append(lon)
            valid_lat.append(lat)

    return valid_lon, valid_lat

# test url
# uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2014.nc'
# uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/0y2w3/0y2w3h2012.nc'
class GNSSRManager(models.Manager):
    def add_gnssr_data_from_file(self, uri, period_days=1):
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
        pp = Platform.objects.get(short_name='GPS')
        ii = Instrument.objects.get(short_name = 'GNSS RECEIVER')
        src = Source.objects.get_or_create(platform = pp, instrument = ii)[0]
        dc = DataCenter.objects.get(short_name = 'U-SOTON/NOC')
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

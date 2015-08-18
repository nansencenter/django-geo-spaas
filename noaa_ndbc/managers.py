#-------------------------------------------------------------------------------
# Name:		managers.py
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	21.01.2015
# Last modified:21.01.2015 19:34
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import numpy as np
import datetime
from netCDF4 import Dataset

from noaa_ndbc.models import *

class StdMetMeasurementManager(models.Manager):
    def get_measurements(polygon, time1, time2):
        buoys = StandardMeteorologicalBuoy.objects.filter(location__coveredby =
                polygon)
        measurements = {}
        for buoy in buoys:
            measurements[buoy.ndbc_id] = []
            years = np.linspace(time1.year, time2.year,
                    time2.year-time1.year+1)
            for year in years:
                try:
                    ds = Dataset(buoy.get_opendap_url(year))
                except RuntimeError as e:
                    print e.message+': '+buoy.get_opendap_url(year)
                    continue
                times = ds.variables['time']
                indices = np.where(times>=calendar.timegm(time1.timetuple())
                        and times<=calendar.timegm(time2.timetuple()))
                for i in indices:
                    measurement = StdMetMeasurement( 
                        buoy = buoy,
                        time = datetime.datetime.utcfromtimestamp(times[i]),
                        wind_from_direction = ds.variables['wind_dir'][i],
                        wind_speed = ds.variables['wind_spd'][i],
                        gust = ds.variables['gust'][i],
                        wave_height = ds.variables['wave_height'][i],
                        dominant_wave_period = ds.variables['dominant_wpd'][i])
                    measurements[buoy.ndbc_id].append(measurement)
        return measurements

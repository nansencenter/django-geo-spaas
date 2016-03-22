#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:
#
# Created:
# Last modified:
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry

import netCDF4
from thredds_crawler.crawl import Crawl
from nansencloud.noaa_ndbc.models import StandardMeteorologicalBuoy

class Command(BaseCommand):
    args = '<year>'
    help = 'Add buoy metadata to archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide a year')
        url='http://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/catalog.xml'
        year = int(args[0])
        # Create regex string
        regex = '(.*%s\.nc)' %year
        c = Crawl(url, select=[regex])
        added = 0
        for ds in c.datasets:
            url = [s.get('url') for s in ds.services if
                    s.get('service').lower()=='opendap'][0]
            nc_dataset = netCDF4.Dataset(url)
            station = nc_dataset.station
            longitude = nc_dataset.variables['longitude']
            latitude = nc_dataset.variables['latitude']
            location = GEOSGeometry('POINT(%s %s)' %(longitude[0],latitude[0]))
            ndbc_stdmet = StandardMeteorologicalBuoy(
                    station = station,
                    location = location,
                    year = year,
                    opendap = url
                )
            ndbc_stdmet.save()
            added += 1

        self.stdout.write(
                'Successfully added meta data of %s stdmet buouy datasets'
                %added)

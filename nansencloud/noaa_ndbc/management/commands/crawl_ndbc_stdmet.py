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
            raise IOError('Please provide URL')
        #url='http://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/catalog.xml'
        url = args[0]
        if len(args)==1:
            select = None
        else:
            year = int(args[1])
            select = ['(.*%s\.nc)' % year]
        c = Crawl(url, select=select, skip=['.*ncml'], debug=True)
        added = 0
        for ds in c.datasets:
            url = [s.get('url') for s in ds.services if
                    s.get('service').lower()=='opendap'][0]

            ndbc_stdmet, cr = StandardMeteorologicalBuoy.objects.get_or_create(url)
            if cr:
                print url
                added += 1

        self.stdout.write(
                    'Successfully added meta data of %s stdmet buouy datasets'
                    %added)

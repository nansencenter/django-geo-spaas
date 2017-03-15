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
import os
import time
import re
import urllib2

from django.core.management.base import BaseCommand, CommandError

from geospaas.nansat_ingestor.management.commands.ingest import Command as IngestCommand

# extend Ingest
class Command(IngestCommand):
    args = 'HYRAX_URL'
    help = 'Add file to catalog from HYRAX server'

    def handle(self, *args, **options):
        print 'Searching netcdf files. May takes some time...\n\n\n'
        nc_uris = find_netcdf_uris(args[0])
        super(Command, self).handle(*nc_uris, **options)
            

def find_netcdf_uris(uri0, sleep=0.5):
    uri0_base = os.path.split(uri0)[0]
    print 'Search in ', uri0_base
    # get HTML from the URL
    time.sleep(sleep)
    response = urllib2.urlopen(uri0)
    html = response.read()
    
    # find all links to netDCF
    nc_uris = [os.path.join(uri0_base, uri.replace('href="', '').replace('.nc.dds', '.nc'))
            for uri in re.findall('href=.*nc\.dds', html)]
    
    # find all links to sub-pages
    uris = [os.path.join(uri0_base, uri.replace('href="', ''))
            for uri in re.findall('href=.*/contents.html', html)]
    # get links to netcDF also from sub-pages
    for uri in uris:
        nc_uris += find_netcdf_uris(uri)
    # return all links to netCDF
    return nc_uris

    

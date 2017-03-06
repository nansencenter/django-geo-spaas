from django.contrib.gis.geos import GEOSGeometry

import netCDF4
from thredds_crawler.crawl import Crawl
from geospaas.noaa_ndbc.models import StandardMeteorologicalBuoy

#def populate_stdmbuoys():


def crawl(*args, **options):
    if len(args)==0:
        raise IOError('Please provide URL')
    url = args[0]
    if len(args)==2:
        try:
            select = ['(.*%s\.nc)' % int(args[1])]
        except ValueError:
            select = ['(.*%s)' %args[1]]
    else:
        select = None
    c = Crawl(url, select=select, skip=['.*ncml'], debug=True)
    added = 0
    for ds in c.datasets:
        url = [s.get('url') for s in ds.services if
                s.get('service').lower()=='opendap'][0]
        ndbc_stdmet, cr = StandardMeteorologicalBuoy.objects.get_or_create(url)
        if cr:
            print url
            added += 1
    return added

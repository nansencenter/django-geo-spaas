#!/usr/bin/env python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nansencloud.settings")

import django
django.setup()

from nansatcat.models import *
from nansatcat.forms import *
from nansatcat.views import *

from nansatproc.models import *
from nansatproc.forms import *
from nansatproc.views import *

from django.contrib.gis.geos import GEOSGeometry

import glob
import time
import datetime

from sadcat import *

def remove_unexisting(sensor=''):
    ''' Remove duplicates, unexsiting data '''
    # remove
    images = Image.objects.all()
    if sensor != '':
        images = images.filter(sensor__name=sensor)
    dbFiles = images.values_list('filename__name', 'filename__path__name')


def migrate_image(sensor, maxfiles=None):
    '''Copy data from sadcat database'''
    cic = CommonImagesCatalog()
    oldFiles = cic.get_sensor_list(sensor)[0]
    print 'Input images:', len(oldFiles)
    sensors = {'meris': ['MERIS', 'ENVISAT'],
               'radarsat2': ['SAR', 'Radarsat2']}
    sensorName = sensors[sensor][0]
    sensorSat = sensors[sensor][1]
    # get all images in DB
    dbFiles = Filename.objects.all()

    for of in oldFiles[:maxfiles]:
        ifilename = Filename.create(os.path.join(of[1].strip(), of[0].strip()))
        print ifilename,
        if ifilename in dbFiles:
            print '... already there.'
            continue
        i = Image.create(str(ifilename),
                        sensorName,
                        of[3],
                        of[3]+datetime.timedelta(0.1),
                        GEOSGeometry(of[4]),
                        satellite=sensorSat,
                        mapper='')
        i.save()
        print '... saved!'


def fill_database(input_files, mapper='', sensor=''):
    ''' Fill the table Image with core info on satellite images'''
    # get list of all filenames and pathname from DB
    images = Image.objects.all()
    if sensor is not '':
        images = images.filter(sensor__name=sensor)

    # convert to list of full filenames
    newFiles = images.new_sourcefiles(input_files)
    # add new files
    t0 = time.time()
    for n, newFile in enumerate(newFiles):
        i, cr = Image.objects.get_or_create(newFile, mapper=mapper)
        t1 = time.time()
        dt = (t1 - t0) / (n + 1) # time per record
        print '%05d/%05d %s saved (%5.2f/%5.2f)' % (n,
                                              len(newFiles),
                                              newFile,
                                              t1-t0,
                                              dt * len(newFiles) - dt * (n + 1))

def process(crit, TheModel, opts=None, force=False):
    # get all images
    qs = Image.objects.all()

    # filter by filename
    if crit.has_key('filename') and crit['filename'] is not None:
        qs = qs.filter(sourcefile__name__iexact=crit['filename'])

    # filter by sensor
    if crit.has_key('sensor') and crit['sensor'] is not None:
        qs = qs.filter(sensor__name__exact=crit['sensor'].capitalize())

    # filter by satellite
    if crit.has_key('satellite') and crit['satellite'] is not None:
        qs = qs.filter(satellite__name__exact=crit['satellite'].capitalize())

    # filter by start_date
    if crit.has_key('period_start') and crit['period_start'] is not None:
        qs = qs.filter(start_date__gte=crit['period_start'])

    # filter by stop_date
    if crit.has_key('period_end') and crit['period_end'] is not None:
        qs = qs.filter(start_date__lt=crit['period_end'])

    print qs

    if not force:
        newFiles = TheModel.objects.new_sourcefiles(qs.sourcefiles())
        print newFiles
    else:
        newFiles = qs.sourcefiles()

    for newFile in newFiles:
        i, cr = TheModel.create(newFile)
        print newFile, cr
        status = i.process(opts, force=force)
        if status ==0:
            i.save()

## get images in the dir
#inp_files = glob.glob('/Data/sat/downloads/MERIS/MER_FRS_1*.N1')
#inp_files = glob.glob('/Data/sat/downloads/MERIS/MER_FRS_1*201108??_*.N1')
#inp_files.sort()
#fill_database(inp_files[:100], 'meris_l1', 'Meris')
#

#inp_files = glob.glob('/Data/sat/downloads/Radarsat2/RS2*_2014102?_*.zip')
#inp_files.sort()
#fill_database(inp_files[:5], 'radarsat2', 'Radarsat2')

#
## process selected Meris images for Web
#criteria = {
#    'filename'   : None,
#    'sensor'     : 'Meris',
#    'period_start' : datetime.datetime(2002, 1, 1),
#    'period_end'  : datetime.datetime(2012, 3, 28),
#    'border'     : None
#}
#process(criteria, MerisWeb)
#

"""
# get RS2 images
rs2_files = glob.glob('/Data/sat/downloads/Radarsat2/RS2_201408??_*')
rs2_files.sort()
fill_database(rs2_files, 'radarsat2', 'SAR')


# process selected Radarsat2 images for Web
crit = {
    'filename'   : None,
    'satellite'     : 'Radarsat2',
    'period_start' : datetime.datetime(2014, 1, 1),
    'period_end'  : datetime.datetime(2014, 12, 31),
    'border'     : None
}
process(crit, SARWeb, force=True)
"""

## get S1A images

s1a_files = glob.glob('/Data/sat/downloads/Sentinel-1/S1A*.zip')
s1a_files.sort()
fill_database(s1a_files, 's1a_l1', 'SAR')

"""
## process selected Radarsat2 images for Web
crit = {
    'filename'   : 'S1A_IW_GRDH_1SSH_20140819T165234_20140819T165259_002011_001F22_362A.zip',
    'sensor'     : 'SAR',
    'period_start' : datetime.datetime(2014, 8, 1),
    'period_end'  : None,
    'border'     : None
}
process(crit, SARWeb, force=True)
"""
#
## Get ASAR images
#asar_files = glob.glob('/Data/sat/downloads/ASAR/moncoze/ASA_WSM*2011*.N1')
#asar_files.sort()
#fill_database(asar_files, 'asar', 'ASAR')
## process selected Radarsat2 images for Web
#crit = {
#    'filename'   : None,
#    'sensor'     : 'ASAR',
#    'period_start' : datetime.datetime(2011, 1, 1),
#    'period_end'  : datetime.datetime(2011, 1, 31),
#    'border'     : None
#}
#process(crit, SARWeb)
#

"""
dropdb -h postgis -p 5432 -U opengeo geodjango
createdb -h postgis -p 5432 -U opengeo -O opengeo -T template_postgis geodjango
"""


"""
rm geodjango.db
spatialite geodjango.db "SELECT InitSpatialMetaData();"


ogr2ogr --config PG_LIST_ALL_TABLES YES --config PG_SKIP_VIEWS YES -preserve_fid -f "SQLite" geodjango.sqlite -progress PG:"dbname='geodjango' active_schema=public schemas=public host='postgis' port='5432' user='opengeo' password='open2014geo' " -dsco SPATIALITE=yes -gt 65536 -lco LAUNDER=yes -dsco SPATIALITE=yes -lco SPATIAL_INDEX=yes
"""

"""
rm ../../django-nansat-process/nansatproc/migrations -rf
rm ../../django-nansat-catalog/nansatcat/migrations -rf
./manage.py makemigrations nansatcat
./manage.py makemigrations nansatproc
./manage.py migrate
./manage.py createsuperuser --username=antonk --email=
"""

#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	05.12.2014
# Last modified:05.12.2014 16:02
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import time
from cat.models import Image

def add_images(input_files, mapper='', sensor=''):
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



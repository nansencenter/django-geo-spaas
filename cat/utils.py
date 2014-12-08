#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	05.12.2014
# Last modified:05.12.2014 17:09
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import time
from cat.models import Image

def add_image(filename, mapper='', sensor=''):
    ''' Fill the table Image with core info on satellite images'''
    # get list of all filenames and pathname from DB
    images = Image.objects.all()
    if sensor is not '':
        images = images.filter(sensor__name=sensor)

    # convert to list of full filenames
    if not filename in images.sourcefiles():
        # add new file
        i, cr = Image.objects.get_or_create(filename, mapper=mapper)



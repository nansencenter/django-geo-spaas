#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	05.12.2014
# Last modified:08.12.2014 16:31
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import os, time, warnings, glob

from cat.models import Image

def get_images_for_sensor(sensor):
    images = Image.objects.all()
    if sensor is not '':
        images = images.filter(sensor__name=sensor)
    return images

def add_image(filename, mapper='', sensor=''):
    ''' Fill the table Image with core info on satellite images'''
    images = get_images_for_sensor(sensor)

    # convert to list of full filenames
    if not filename in images.sourcefiles():
        # add new file
        i, cr = Image.objects.get_or_create(filename, mapper=mapper)
        return filename
    else:
        raise Exception('Image already added') # make custom exception for this?

def add_images_in_dir(dir, *args, **kwargs):
    '''Add all images in directory dir to cat.models.Image'''
    added_files = []
    for ff in glob.glob(os.path.join(dir,'*.*')):
        if os.path.isfile(ff):
            try:
                added_files.append(add_image(ff, *args, **kwargs))
            except Exception as e:
                warnings.warn(e.message)
                continue
    return added_files

def add_images_in_list(filenames, *args, **kwargs):
    '''Add all images in filenames list to cat.models.Image'''
    added_files = []
    for fn in filenames:
        if os.path.isfile(fn):
            try:
                added_files.append(add_image(fn, *args, **kwargs))
            except Exception as e:
                warnings.warn(e.message)
                continue
    return added_files

def add_images(*args, **kwargs):
    '''
    Add all images *args to cat.models.Image

    Parameters
    ----------
    args : list of filenames, separate filenames, folders
    kwargs: additional keyword arguments for the add_image method
        
    '''
    added_files = []
    for fn in args:
        if os.path.isfile(fn):
            added_files.append(add_image(fn, **kwargs))
        if os.path.isdir(fn):
            added_files.extend(add_images_in_dir(fn, **kwargs))
        if isinstance(fn, list):
            added_files.extend(add_images_in_list(fn, **kwargs))
    return added_files


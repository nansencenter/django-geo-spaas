#-------------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:       Morten Wergeland Hansen
# Modified: Morten Wergeland Hansen
#
# Created:  05.12.2014
# Last modified:08.12.2014 16:31
# Copyright:    (c) NERSC
# License:
#-------------------------------------------------------------------------------
import os, time, warnings, glob

from nansencloud.cat.models import Image

def get_files_from_dir(inputDir):
    ''' Get all input valid files from input directory or wildcard '''

    # get list of entries from wildcard or directory
    if '*' in inputDir or '?' in inputDir:
        globEntries = glob.glob(inputDir)
    elif os.path.isdir(inputDir):
        globEntries = glob.glob(os.path.join(inputDir, '*'))
    else:
        raise TypeError('Wrong input directory or wildcard %s' % inputDir)

    # fetch only files from the found entries
    inputFiles = []
    for globEntry in globEntries:
        if os.path.isfile(globEntry):
            inputFiles.append(globEntry)

    return inputFiles

def get_files_from_list(filenames):
    '''Get all valid input filenames from list'''
    inputFiles = []
    for fn in filenames:
        if os.path.isfile(fn):
            inputFiles.append(fn)

    return inputFiles

def add_images(*args, **kwargs):
    '''
    Add all images *args to nansencloud.cat.models.Image

    Parameters
    ----------
    args : list of filenames, separate filenames, folders
    kwargs: additional keyword arguments for the add_image method

    '''
    # create list with valid input files
    inputFiles = []
    for fn in args:
        if os.path.isfile(fn):
            inputFiles.append(fn)
        elif type(fn) in (tuple, list):
            inputFiles.extend(get_files_from_list(fn))
        else:
            try:
                inputFiles.extend(get_files_from_dir(fn))
            except TypeError as e:
                warnings.warn(e.message)
    inputFiles.sort()

    # get list of files available in the database
    images = Image.objects.all()

    # get list of new files (exiting on disk but not in the database)
    newFiles = images.new_sourcefiles(inputFiles)

    # add new files to the database
    mapper = kwargs.get('mapper', '')
    addedFiles = []
    for newFile in newFiles:
        i, cr = Image.objects.get_or_create(newFile, mapper=mapper)
        addedFiles.append(i.sourcefile.name)

    return addedFiles


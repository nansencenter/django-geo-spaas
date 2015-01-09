#-------------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:       Morten Wergeland Hansen
# Modified:     Anton Korosov
#
# Created:      09.12.2014
# Last modified:09.01.2015
# Copyright:    (c) NERSC
# License:
#-------------------------------------------------------------------------------
from cat.models.image import Image
from proc.models import *

def process(modelName, crit={}, opts=None, force=False):
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

    # convert the model name to Class
    TheModel = eval(modelName)

    if not force:
        newFiles = TheModel.objects.new_sourcefiles(qs.sourcefiles())
    else:
        newFiles = qs.sourcefiles()

    for newFile in newFiles:
        i, cr = TheModel.create(newFile)
        status = i.process(opts, force=force)
        if status==0:
            i.save()

    return newFiles



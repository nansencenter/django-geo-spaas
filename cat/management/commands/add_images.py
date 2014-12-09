#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	05.12.2014
# Last modified:09.12.2014 13:04
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import os, glob, warnings
from django.core.management.base import BaseCommand, CommandError

from nansat.tools import NansatReadError
from cat.utils import add_images

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to image archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')
        added = add_images(*args)
        if len(added)>1:
            ff = ['%s\n'%fn for fn in added]
            self.stdout.write('Successfully added satellite images: \n%s'%ff)
        elif len(added)==1:
            self.stdout.write('Successfully added satellite image: %s'%added)
        else:
            self.stdout.write('Did not add any images')


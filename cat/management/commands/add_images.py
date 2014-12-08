#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	05.12.2014
# Last modified:05.12.2014 17:14
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
from django.core.management.base import BaseCommand, CommandError
from cat.utils import add_image

class Command(BaseCommand):
    args = '<input_file input_file ...>'
    help = 'Add file to image archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')
        for fname in args:
            add_image(fname)
            self.stdout.write('Successfully added satellite image: %s'%fname)


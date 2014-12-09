#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:	Morten Wergeland Hansen
#
# Created:	09.12.2014
# Last modified:09.12.2014 13:12
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
from django.core.management.base import BaseCommand, CommandError

from cat.utils import process

class Command(BaseCommand):
    args = '<procModel>'
    help = 'Process new files in procModel'

    def handle(self, *args, **options):
        if len(args)!=1:
            raise IOError('Please provide a model name')
        process(args[0])
        self.stdout.write('Successfully processed new data in %s model'%args[0])

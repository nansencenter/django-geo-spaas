#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:
#
# Created:
# Last modified:
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import os, glob, warnings
from django.core.management.base import BaseCommand, CommandError

from nansat.tools import NansatReadError
from nansencloud.nansat_ingestor.utils import nansat_ingest

class Command(BaseCommand):
    args = '<file_or_folder file_or_folder ...>'
    help = 'Add file to catalog archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')
        added = nansat_ingest(*args)
        if len(added)>1:
            ff = ['%s\n'%fn for fn in added]
            self.stdout.write('Successfully added: \n%s'%ff)
        elif len(added)==1:
            self.stdout.write('Successfully added: %s'%added)
        else:
            self.stdout.write('Did not add anything')


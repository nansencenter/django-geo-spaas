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
from django.core.management.base import BaseCommand

from nansencloud.utils import uris_from_args
from nansencloud.ingest_gnssr.models import GNSSR

class Command(BaseCommand):
    args = '<filename> <filename> ...'
    help = 'Add buoy metadata to archive'

    def handle(self, *args, **options):
        if len(args)==0:
            raise IOError('Please provide at least one filename')

        uris = uris_from_args(*args)
        for uri in uris:
            GNSSR.objects.add_gnssr_data_from_file(uri)

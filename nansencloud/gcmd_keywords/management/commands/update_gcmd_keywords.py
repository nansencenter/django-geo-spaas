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
from django.core.management.base import BaseCommand, CommandError
from nerscmetadata import gcmd_keywords

from nansencloud.gcmd_keywords.models import Instrument, Platform

class Command(BaseCommand):
    help = 'Get latest NASA Global Change Master Directory keywords'

    def handle(self, *args, **options):
        Instrument.objects.create_from_gcmd_keywords()
        Platform.objects.create_from_gcmd_keywords()
        # TODO: Add remaining lists

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

from geospaas.vocabularies.models import Parameter
from geospaas.vocabularies.models import DataCenter
from geospaas.vocabularies.models import HorizontalDataResolution
from geospaas.vocabularies.models import Instrument
from geospaas.vocabularies.models import ISOTopicCategory
from geospaas.vocabularies.models import Location
from geospaas.vocabularies.models import Platform
from geospaas.vocabularies.models import Project
from geospaas.vocabularies.models import ScienceKeyword
from geospaas.vocabularies.models import TemporalDataResolution
from geospaas.vocabularies.models import VerticalDataResolution

class Command(BaseCommand):
    help = 'Get latest vocabularies'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true',
                            help='''Option to force update vocabularies using remote repository''')

    def handle(self, *args, **options):
        
        Parameter.objects.create_from_vocabularies(**options)
        DataCenter.objects.create_from_vocabularies(**options)
        HorizontalDataResolution.objects.create_from_vocabularies(**options)
        Instrument.objects.create_from_vocabularies(**options)
        ISOTopicCategory.objects.create_from_vocabularies(**options)
        Location.objects.create_from_vocabularies(**options)
        Platform.objects.create_from_vocabularies(**options)
        Project.objects.create_from_vocabularies(**options)
        ScienceKeyword.objects.create_from_vocabularies(**options)
        TemporalDataResolution.objects.create_from_vocabularies(**options)
        VerticalDataResolution.objects.create_from_vocabularies(**options)

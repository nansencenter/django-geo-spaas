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

    def handle(self, *args, **options):
        Parameter.objects.create_from_vocabularies()
        DataCenter.objects.create_from_vocabularies()
        HorizontalDataResolution.objects.create_from_vocabularies()
        Instrument.objects.create_from_vocabularies()
        ISOTopicCategory.objects.create_from_vocabularies()
        Location.objects.create_from_vocabularies()
        Platform.objects.create_from_vocabularies()
        Project.objects.create_from_vocabularies()
        ScienceKeyword.objects.create_from_vocabularies()
        TemporalDataResolution.objects.create_from_vocabularies()
        VerticalDataResolution.objects.create_from_vocabularies()

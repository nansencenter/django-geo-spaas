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

from nansencloud.vocabularies.models import Parameter
from nansencloud.vocabularies.models import DataCenter
from nansencloud.vocabularies.models import HorizontalDataResolution
from nansencloud.vocabularies.models import Instrument
from nansencloud.vocabularies.models import ISOTopicCategory
from nansencloud.vocabularies.models import Location
from nansencloud.vocabularies.models import Platform
from nansencloud.vocabularies.models import Project
from nansencloud.vocabularies.models import ScienceKeyword
from nansencloud.vocabularies.models import TemporalDataResolution
from nansencloud.vocabularies.models import VerticalDataResolution

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

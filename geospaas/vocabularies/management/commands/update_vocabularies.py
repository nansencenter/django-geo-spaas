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
import argparse

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


class StoreDictAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        result = {}
        for key_value_string in values:
            key, value = key_value_string.split('=')
            result[key] = value
        setattr(namespace, self.dest, result)


class Command(BaseCommand):
    help = 'Put vocabularies into the database'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true',
                            help='''Force update of vocabularies from remote repositories''')
        parser.add_argument('--versions', nargs='+', action=StoreDictAction,
                            metavar='VOCABULARY_NAME=VERSION',
                            help='pythesint vocabularies versions to use')

    def handle(self, *args, **options):
        models = [
            Parameter,
            DataCenter,
            HorizontalDataResolution,
            Instrument,
            ISOTopicCategory,
            Location,
            Platform,
            Project,
            ScienceKeyword,
            TemporalDataResolution,
            VerticalDataResolution]

        for model in models:
            model.objects.create_from_vocabularies(**options)

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

from django.core.management.base import BaseCommand

from geospaas.vocabularies.managers import KeywordManager, ParameterManager
from geospaas.vocabularies.models import Keyword, Parameter


class StoreDictAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        result = {}
        for key_value_string in values:
            key, value = key_value_string.split('=')
            result[key] = value
        setattr(namespace, self.dest, result)


class Command(BaseCommand):
    help = 'Put vocabularies into the database'
    models = [
        Keyword,
        Parameter,
    ]

    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true',
                            help='''Force update of vocabularies from remote repositories''')
        parser.add_argument('--versions', nargs='+', action=StoreDictAction,
                            metavar='VOCABULARY_NAME=VERSION',
                            help='pythesint vocabularies versions to use')

    def handle(self, *args, **options):
        for model in self.models:
            model.objects.create_from_vocabularies(**options)

#!/usr/bin/env python
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
#This file mainly exists to allow the following commands to work:
# python setup.py test
# ./runtests <appName>
import os, sys
import argparse

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
sys.path.insert(0, 'project')

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings

def runtests(moduleName=None):
    if moduleName is None:
        appPath = 'geospaas'
    else:
        appPath = 'geospaas.%s' % moduleName

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests([appPath])
    sys.exit(failures)

if __name__ == '__main__':
    # get name of a module to test
    parser = argparse.ArgumentParser()
    parser.add_argument('module', type=str, nargs='?', default=None)
    args = parser.parse_args()

    runtests(args.module)

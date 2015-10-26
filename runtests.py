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
#This file mainly exists to allow 'python setup.py test' to work.
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
sys.path.insert(0, 'project')

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings

def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['nansencloud'])
    sys.exit(failures)

if __name__ == '__main__':
    runtests()

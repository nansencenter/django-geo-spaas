#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Name: runtests.py
# Purpose: test runner to test reusable applications. See:
# https://docs.djangoproject.com/en/dev/topics/testing/advanced/#testing-reusable-applications
#
# Author:       Morten Wergeland Hansen, Anton Korosov
#
# Copyright:    (c) NERSC
# License:
#-------------------------------------------------------------------------------


import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(["geospaas.catalog",
                                      "geospaas.vocabularies"])
    sys.exit(bool(failures))

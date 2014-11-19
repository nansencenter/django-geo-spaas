#!/usr/bin/env python
import sys
import os

sys.path.append('/home/antonk/sadcat/djangosat')
#os.environ['DJANGO_SETTINGS_MODULE'] = 'djangosat.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangosat.settings")

import django
django.setup()

from nansatcat.models import *
from nansatcat.forms import *
from nansatcat.views import *

from nansatproc.models import *
from nansatproc.forms import *
from nansatproc.views import *

from django.contrib.gis.geos import GEOSGeometry

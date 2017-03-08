import os
import numpy as np
import warnings

from django.db import models

from django.conf import settings
from django.contrib.gis.geos import WKTReader

from nansat.nsr import NSR
from nansat.domain import Domain
from nansat.nansat import Nansat

class DatasetManager(models.Manager):
    pass

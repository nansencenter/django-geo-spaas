import os
import warnings

import numpy as np
from scipy.ndimage.filters import gaussian_filter

from django.db import models

from django.conf import settings
from geospaas.utils import uris_from_args
from geospaas.catalog.models import (Dataset, GeographicLocation,
    DataCenter, ISOTopicCategory, DatasetURI)

from nansat import Nansat

from sea_ice_drift.ftlib import feature_tracking
from sea_ice_drift.pmlib import get_distance_to_nearest_keypoint

class SARPairManager(models.Manager):
    def get_or_create(self, uri1, uri2, product_path, *args, **kwargs):
        obj1 = Dataset.objects.get(dataseturi__uri=uri1)
        obj2 = Dataset.objects.get(dataseturi__uri=uri2)

        # check if SARPair already exists
        ds = Dataset.objects.filter(entry_title='SAR_UINT8_PAIR',
                    time_coverage_start=obj1.time_coverage_start,
                    time_coverage_end=obj2.time_coverage_end)
        if ds.count() > 0:
            return ds.first(), False
        print 'Add pair', obj1.time_coverage_start, obj2.time_coverage_end
        # create and save SARPair object in the database
        geolocation = GeographicLocation.objects.get_or_create(
            geometry=obj1.geographic_location.geometry.intersection(
                     obj2.geographic_location.geometry))[0]
        ds = Dataset(
            entry_title='SAR_UINT8_PAIR',
            ISO_topic_category = ISOTopicCategory.objects.get(name='Oceans'),
            data_center = DataCenter.objects.get(short_name='NERSC'),
            summary = 'Pair of SAR images for ice drift',
            time_coverage_start=obj1.time_coverage_start,
            time_coverage_end=obj2.time_coverage_end,
            source=obj1.source,
            geographic_location=geolocation)
        ds.save()
        
        # run Feature Tracking
        print 'Run feature tracking'
        filename1 = uri1.replace('file://localhost', '')
        filename2 = uri2.replace('file://localhost', '')
        n1 = Nansat(filename1)
        n2 = Nansat(filename2)
        x1, y1, x2, y2 = feature_tracking(n1, n2, ratio_test=0.7)
        dist = get_distance_to_nearest_keypoint(x1, y1, n1.shape())
        dist = gaussian_filter(dist, 5)[::5, ::5] / 2.
        dist[dist > 255] = 255
        
        # save results and add dataset URI
        ofilename = os.path.join(product_path,
            '%s_%s.npz' % (os.path.basename(uri1),
                           os.path.basename(uri2)))
        np.savez(ofilename, x1=x1.astype(np.int16),
                           y1=y1.astype(np.int16),
                           x2=x2.astype(np.int16), 
                           y2=y2.astype(np.int16),
                           dist=dist.astype(np.uint8))

        ds_uri = DatasetURI.objects.get_or_create(uri=uris_from_args(ofilename), dataset=ds)[0]
        return ds, True

'''
Utility functions for processing Doppler from multiple SAR acquisitions
'''
import datetime
import numpy as np
from nansat.nansat import Nansat

from django.utils import timezone

from nansencloud.catalog.models import Dataset, DatasetURI

# Start as script
t0 = datetime.datetime(2010,1,1,0,0,0, tzinfo=timezone.utc)
t1 = datetime.datetime(2010,1,2,0,0,0, tzinfo=timezone.utc)

asar = Dataset.objects.filter(source__platform__short_name='ENVISAT',
        source__instrument__short_name='ASAR')
asar_dop = asar.filter(parameters__short_name='dca',
        time_coverage_start__gte=t0, time_coverage_start__lt=t1)

swath3_files = []
for dd in asar_dop:
    try:
        swath3_files.append(dd.dataseturi_set.get(uri__endswith='subswath3.nc').uri)
    except DatasetURI.DoesNotExist:
        continue

valid_land = np.array([])
for ff in swath3_files:
    n = Nansat(ff)
    view_bandnum = n._get_band_number({
        'standard_name': 'sensor_view_angle'
    })
    std_bandnum = n._get_band_number({
        'standard_name': \
            'standard_deviation_of_surface_backwards_doppler_centroid_frequency_shift_of_radar_wave',
    })
    pol = n.get_metadata(bandID=std_bandnum, key='polarization')

    if valid_land.shape==(0,):
        valid_land = n['valid_land_doppler'][n['valid_land_doppler'].any(axis=1)]
        dca = n['dca'][n['valid_land_doppler'].any(axis=1)]
        view_angle = n[view_bandnum][n['valid_land_doppler'].any(axis=1)]
        std_dca = n[std_bandnum][n['valid_land_doppler'].any(axis=1)]
    else:
        vn = n['valid_land_doppler'][n['valid_land_doppler'].any(axis=1)]
        dcan = n['dca'][n['valid_land_doppler'].any(axis=1)]
        view_angle_n = n[view_bandnum][n['valid_land_doppler'].any(axis=1)]
        std_dca_n = n[std_bandnum][n['valid_land_doppler'].any(axis=1)]
        if not vn.shape==valid_land.shape:
            # Resize arrays - just for visual inspection. Actual interpolation
            # is view angle vs doppler anomaly
            if vn.shape[1] > valid_land.shape[1]:
                valid_land = np.resize(valid_land, (valid_land.shape[0],
                    vn.shape[1]))
                dca = np.resize(dca, (dca.shape[0],
                    vn.shape[1]))
                view_angle = np.resize(view_angle, (view_angle.shape[0],
                    vn.shape[1]))
                std_dca = np.resize(std_dca, (std_dca.shape[0],
                    vn.shape[1]))
            if vn.shape[1] < valid_land.shape[1]:
                vn = np.resize(vn, (vn.shape[0], valid_land.shape[1]))
                dcan = np.resize(dcan, (dcan.shape[0], valid_land.shape[1]))
                view_angle_n = np.resize(view_angle_n, (view_angle_n.shape[0], valid_land.shape[1]))
                std_dca_n = np.resize(std_dca_n, (std_dca_n.shape[0], valid_land.shape[1]))
        valid_land = np.concatenate((valid_land, vn))
        dca = np.concatenate((dca, dcan))
        view_angle = np.concatenate((view_angle, view_angle_n))
        std_dca = np.concatenate((std_dca, std_dca_n))

        # Set dca, view_angle and std_dca to nan where not land



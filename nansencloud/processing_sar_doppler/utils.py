'''
Utility functions for processing Doppler from multiple SAR acquisitions
'''
import os, datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
from scipy.interpolate import UnivariateSpline

from nansat.nsr import NSR
from nansat.domain import Domain
from nansat.nansat import Nansat
from sardoppler.sardoppler import Doppler

from django.utils import timezone

from nansencloud.utils import nansat_filename, media_path, product_path
from nansencloud.catalog.models import Dataset, DatasetURI

# Start as script
t0 = datetime.datetime(2010,1,2,0,0,0, tzinfo=timezone.utc)
t1 = datetime.datetime(2010,1,3,0,0,0, tzinfo=timezone.utc)

asar = Dataset.objects.filter(source__platform__short_name='ENVISAT',
        source__instrument__short_name='ASAR')
asar_dop = asar.filter(parameters__short_name='dca',
        time_coverage_start__gte=t0, time_coverage_start__lt=t1)

swath2_files = []
for dd in asar_dop:
    try:
        swath2_files.append(dd.dataseturi_set.get(uri__endswith='subswath2.nc').uri)
    except DatasetURI.DoesNotExist:
        continue

valid_land = np.array([])
for ff in swath2_files:
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
dca[valid_land==0] = np.nan
std_dca[valid_land==0] = np.nan
view_angle[valid_land==0] = np.nan

dca = dca.flatten()
std_dca = std_dca.flatten()
view_angle = view_angle.flatten()

dca = np.delete(dca, np.where(np.isnan(dca)))
std_dca = np.delete(std_dca, np.where(np.isnan(std_dca)))
view_angle = np.delete(view_angle, np.where(np.isnan(view_angle)))

ind = np.argsort(view_angle)
view_angle = view_angle[ind]
dca = dca[ind]
std_dca = std_dca[ind]

# Show this in presentation:
count, anglebins, dcabins, im = plt.hist2d(view_angle, dca, 70, cmin=1,
        range=[[np.min(view_angle), np.max(view_angle)], [0, 170]])
dcabins_grid, anglebins_grid = np.meshgrid(dcabins[:-1], anglebins[:-1])
anglebins_vec = anglebins_grid[count>500]
dcabins_vec = dcabins_grid[count>500]

def f2(x, a, b, c, d, e, f):
    return a + b*x + c*x**2 + d*x**3 + e*np.sin(x) + f*np.cos(x)

guess = [.1,.1,.1,.1,.1,.1]
[a,b,c,d,e,f], params_cov = optimize.curve_fit(f2, anglebins_vec, dcabins_vec, guess)

n = Doppler(swath2_files[0])
van = np.mean(n['sensor_view'], axis=0)
plt.close()
plt.plot(van, f2(van,a,b,c,d,e,f), 'r--')
plt.plot(anglebins_vec, dcabins_vec, '.')
plt.show()

for ff in swath2_files:
    n = Doppler(ff)
    rb = f2(n['sensor_view'], a, b, c, d, e, f)
    fdg = n['dca'] - rb
    n.add_band(array=fdg,
        parameters={'wkv':
            'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'}
        )
    # Reproject to leaflet projection
    xlon, xlat = n.get_corners()
    dom = Domain(NSR(3857),
            '-lle %f %f %f %f -tr 1000 1000' % (
                xlon.min(), xlat.min(), xlon.max(), xlat.max()))
    n.reproject(dom, eResampleAlg=1, tps=True)

    band = 'fdg'
    i = 2
    filename = '%s_subswath_%d.png'%(band, i)

    module = 'nansencloud.processing_sar_doppler'
    fn = '/mnt/10.11.12.232/sat_downloads_asar/level-0/2010-01/gsar_rvl/' \
            + n.fileName.split('/')[-2]+'.gsar'
    mp = media_path(module, fn)

    # Update figure
    n.write_figure(os.path.join(mp, filename),
                clim = [-200,200],
                bands=band+'_000',
                mask_array=n['swathmask'],
                mask_lut={0:[128,128,128]}, transparency=[128,128,128])





#weight = 1./std_dca
#weight[np.isinf(weight)] = 0
#rbinterp = UnivariateSpline(
#        view_angle,
#        dca,
#        w = weight, 
#        k = 4 #kk[self.get_metadata()['subswath']]
#    )
#
#y = rbinterp(view_angle)
#rbfull = y.reshape(view_angle.shape)

## could check columns and set those with delta>3 Hz invalid:
#delta = rb - rbinterp(va)

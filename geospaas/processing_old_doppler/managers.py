import os
from math import sin, pi, cos, acos, copysign
import numpy as np

from dateutil.parser import parse
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.contrib.gis.geos import WKTReader

from geospaas.utils import nansat_filename, media_path, product_path
from geospaas.vocabularies.models import Parameter
from geospaas.catalog.models import DatasetParameter, GeographicLocation
from geospaas.catalog.models import Dataset, DatasetURI
from geospaas.viewer.models import Visualization
from geospaas.viewer.models import VisualizationParameter
from geospaas.nansat_ingestor.managers import DatasetManager as DM

from nansat.nsr import NSR
from nansat.domain import Domain
from nansat.nansat import Nansat

class DatasetManager(DM):

    def get_or_create(self, uri, reprocess=False, *args, **kwargs):
        # ingest file to db
        ds, created = super(DatasetManager, self).get_or_create(uri, *args,
                **kwargs)
        if not created and not reprocess:
            return ds, created

        # set Dataset entry_title
        ds.entry_title = 'old Envisat ASAR Doppler'
        ds.save()

        fn = nansat_filename(uri)
        #try:
        n = Nansat(fn)

        mm = self.__module__.split('.')
        module = '%s.%s' %(mm[0],mm[1])
        mp = media_path(module, n.fileName)
        ppath = product_path(module, n.fileName)

        fdg = n['dop_coef_observed'] - n['dop_coef_predicted'] \
                - n['azibias'] - n['range_bias_scene']
        fdg[fdg>200] = np.nan
        n.add_band(array=fdg,
            parameters={'wkv':
                'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'})

        n.export('fdg.nc', bands=['fdg_000'])
        nn = Nansat('fdg.nc')

        # Reproject to leaflet projection
        xlon, xlat = nn.get_corners()
        d = Domain(NSR(3857),
                '-lle %f %f %f %f -tr 1000 1000' % (
                    xlon.min(), xlat.min(), xlon.max(), xlat.max()))
        nn.reproject(d, eResampleAlg=1, tps=True)

        band = 'fdg'
        filename = '_%s.png'%band
        # check uniqueness of parameter
        param = Parameter.objects.get(short_name = band)
        nn.write_figure(os.path.join(mp, filename),
            bands=band+'_000',
            mask_array=nn['swathmask'],
            mask_lut={0:[128,128,128]}, transparency=[128,128,128]
        )

        # Get DatasetParameter
        dsp, created = DatasetParameter.objects.get_or_create(dataset=ds,
                    parameter = param)

        # Create Visualization
        geom, created = GeographicLocation.objects.get_or_create(
                    geometry=WKTReader().read(nn.get_border_wkt()))
        vv, created = Visualization.objects.get_or_create(
                uri='file://localhost%s/%s' % (mp, filename),
                title='%s (old doppler)' %param.standard_name,
                geographic_location = geom
            )

        # Create VisualizationParameter
        vp, created = VisualizationParameter.objects.get_or_create(
                visualization=vv, ds_parameter=dsp
            )

        return ds, True
       # except:
       #     return 0, False

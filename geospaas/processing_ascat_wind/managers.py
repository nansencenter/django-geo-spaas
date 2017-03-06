import os
import numpy as np

from nansat.nansat import Nansat
from nansat.nsr import NSR
from nansat.domain import Domain

from django.contrib.gis.geos import WKTReader

from nansencloud.vocabularies.models import Parameter
from nansencloud.catalog.models import DatasetParameter, GeographicLocation
from nansencloud.viewer.models import Visualization
from nansencloud.viewer.models import VisualizationParameter
from nansencloud.nansat_ingestor.managers import DatasetManager as DM
from nansencloud.utils import nansat_filename, media_path, product_path


class DatasetManager(DM):

    def get_or_create(self, uri, reprocess=False, *args, **kwargs):
        # ingest file to db
        ds, created = super(DatasetManager, self).get_or_create(uri, *args,
                **kwargs)

        fn = nansat_filename(uri)

        n = Nansat(fn)

        # Reproject to leaflet projection
        xlon, xlat = n.get_corners()
        d = Domain(NSR(3857),
            '-lle %f %f %f %f -tr 1000 1000' % (
                xlon.min(), xlat.min(), xlon.max(), xlat.max()))
        n.reproject(d)

        # Get band numbers of required bands according to standard names
        speedBandNum = n._get_band_number({'standard_name': 'wind_speed'})
        dirBandNum = n._get_band_number({'standard_name': 'wind_from_direction'})
        
        # Get numpy arrays of the bands
        speed = n[speedBandNum]
        dir = n[dirBandNum]

        ## It probably wont work with nansatmap...
        #nmap = Nansatmap(n, resolution='l')
        #nmap.pcolormesh(speed, vmax=18)
        #nmap.quiver(-speed*np.sin(dir), speed*np.cos(dir), step=10, scale=300,
        #        width=0.002)

        # Set paths - this code should be inherited but I think there is an
        # issue in generalising the first line that defines the current module
        mm = self.__module__.split('.')
        module = '%s.%s' %(mm[0],mm[1])
        mp = media_path(module, n.fileName)
        ppath = product_path(module, n.fileName)

        filename = os.path.basename(n.fileName).split('.')[0] + '.' + \
                os.path.basename(n.fileName).split('.')[1] + '.png'

        # check uniqueness of parameter
        param1 = Parameter.objects.get(standard_name =
                n.get_metadata(bandID=speedBandNum, key='standard_name'))
        param2 = Parameter.objects.get(standard_name =
                n.get_metadata(bandID=dirBandNum, key='standard_name'))

        n.write_figure(os.path.join(mp, filename), bands=speedBandNum,
                mask_array=n['swathmask'], mask_lut={0:[128,128,128]},
                transparency=[128,128,128])

        # Get DatasetParameter
        dsp1, created = DatasetParameter.objects.get_or_create(dataset=ds,
                parameter = param1)

        # Create Visualization
        geom, created = GeographicLocation.objects.get_or_create(
                geometry=WKTReader().read(n.get_border_wkt()))
        vv, created = Visualization.objects.get_or_create(
                uri='file://localhost%s/%s' % (mp, filename),
                title='%s' %(param1.standard_name),
                geographic_location = geom
            )

        # Create VisualizationParameter
        vp, created = VisualizationParameter.objects.get_or_create(
                visualization=vv,
                ds_parameter=dsp1
            )

        return ds, True

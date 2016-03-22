import os
from math import sin, pi, cos, acos, copysign
import numpy as np

from dateutil.parser import parse
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.contrib.gis.geos import WKTReader

from nansencloud.utils import nansat_filename, media_path
from nansencloud.vocabularies.models import Parameter
from nansencloud.catalog.models import DatasetParameter, GeographicLocation
from nansencloud.catalog.models import Dataset, DatasetURI
from nansencloud.viewer.models import Visualization
from nansencloud.viewer.models import VisualizationParameter
from nansencloud.nansat_ingestor.managers import DatasetManager as DM

# This should probably be done differently..
from nansencloud.processing_sar.tools import nansatFigure

from nansat.nsr import NSR
from nansat.domain import Domain
from sardoppler.sardoppler import Doppler


class DatasetManager(DM):

    def get_or_create(self, uri, *args, **kwargs):
        # ingest file to db
        super(DatasetManager, self).get_or_create(uri, *args, **kwargs)

        # Get geolocation of dataset - this must be updated
        ds = self.filter(dataseturi__uri=uri)[0]
        geoloc = ds.geographic_location

        # Update dataset border #
        n_subswaths = 5
        fn = nansat_filename(uri)
        swath_data = {}
        lon = {}
        lat = {}
        astep = {}
        rstep = {}
        az_left_lon = {}
        ra_upper_lon = {}
        az_right_lon = {}
        ra_lower_lon = {}
        az_left_lat = {}
        ra_upper_lat = {}
        az_right_lat = {}
        ra_lower_lat = {}
        num_border_points = 10
        border = 'POLYGON(('
        for i in range(n_subswaths):
            # Read subswaths 
            swath_data[i] = Doppler(fn, subswath=i)
            # Should use nansat.domain.get_border, but it must become easier to
            # use - see nansat issue #166
            # (https://github.com/nansencenter/nansat/issues/166)
            lon[i], lat[i] = swath_data[i].get_geolocation_grids()
            astep[i] = max(1, (lon[i].shape[0]/2*2-1) / num_border_points)
            rstep[i] = max(1, (lon[i].shape[1]/2*2-1) / num_border_points)
            az_left_lon[i] = lon[i][0:-1:astep[i],0]
            az_left_lat[i] = lat[i][0:-1:astep[i],0]
            az_right_lon[i] = lon[i][0:-1:astep[i],-1]
            az_right_lat[i] = lat[i][0:-1:astep[i],-1]
            ra_upper_lon[i] = lon[i][-1,0:-1:rstep[i]] 
            ra_upper_lat[i] = lat[i][-1,0:-1:rstep[i]]
            ra_lower_lon[i] = lon[i][0,0:-1:rstep[i]]
            ra_lower_lat[i] = lat[i][0,0:-1:rstep[i]] 
            #ra_upper_lon[i] = lon[i][-1,0] 
            #ra_upper_lat[i] = lat[i][-1,0]
            #ra_lower_lon[i] = lon[i][0,0]
            #ra_lower_lat[i] = lat[i][0,0] 
            assert len(az_left_lon[i])==11
            assert len(az_right_lon[i])==11
            assert len(az_left_lat[i])==11
            assert len(az_right_lat[i])==11
            assert len(ra_upper_lon[i])==11
            assert len(ra_lower_lon[i])==11
            assert len(ra_upper_lat[i])==11
            assert len(ra_lower_lat[i])==11
            #assert np.isscalar(ra_upper_lon[i])
            #assert np.isscalar(ra_lower_lon[i])
            #assert np.isscalar(ra_upper_lat[i])
            #assert np.isscalar(ra_lower_lat[i])

        # Solve problem with swath overlaps...
        ##vecfilt = lamdba x,y: x[x>y] if np.all(gg_lon>0) else x[x<y]
        ##gg_lon = np.gradient(ra_upper_lon[0])
        ##assert np.all(gg_lon>0) or np.all(gg_lon<0)
        ##upper_lons = np.concatenate((az_left_lon[0], ra_upper_lon[0], 
        ##        vecfilt(ra_upper_lon[1],ra_upper_lon[0][-1]),
        ##        vecfilt(ra_upper_lon[2],ra_upper_lon[1][-1]),
        ##        vecfilt(ra_upper_lon[3],ra_upper_lon[2][-1]),
        ##        vecfilt(ra_upper_lon[4],ra_upper_lon[3][-1])))
        #lons = np.concatenate((az_left_lon[0], [ra_upper_lon[0]],
        #    [ra_upper_lon[1]], [ra_upper_lon[2]], [ra_upper_lon[3]],
        #    [ra_upper_lon[4]], np.flipud(az_right_lon[4]), [ra_lower_lon[4]],
        #    [ra_lower_lon[3]], [ra_lower_lon[2]], [ra_lower_lon[1]],
        #    [ra_lower_lon[0]]))
        lons = np.concatenate((az_left_lon[0], ra_upper_lon[0],
            ra_upper_lon[1], ra_upper_lon[2], ra_upper_lon[3],
            ra_upper_lon[4], np.flipud(az_right_lon[4]),
            np.flipud(ra_lower_lon[4]),
            np.flipud(ra_lower_lon[3]), np.flipud(ra_lower_lon[2]),
            np.flipud(ra_lower_lon[1]),
            np.flipud(ra_lower_lon[0])))
        # apply 180 degree correction to longitude - code copied from
        # get_border_wkt...
        for ilon, llo in enumerate(lons):
            lons[ilon] = copysign(acos(cos(llo * pi / 180.)) / pi * 180,
                    sin(llo * pi / 180.))
        #lats = np.concatenate((az_left_lat[0], [ra_upper_lat[0]],
        #    [ra_upper_lat[1]], [ra_upper_lat[2]], [ra_upper_lat[3]],
        #    [ra_upper_lat[4]], np.flipud(az_right_lat[4]), [ra_lower_lat[4]],
        #    [ra_lower_lat[3]], [ra_lower_lat[2]], [ra_lower_lat[1]],
        #    [ra_lower_lat[0]]))
        lats = np.concatenate((az_left_lat[0], ra_upper_lat[0],
            ra_upper_lat[1], ra_upper_lat[2], ra_upper_lat[3],
            ra_upper_lat[4], np.flipud(az_right_lat[4]),
            np.flipud(ra_lower_lat[4]),
            np.flipud(ra_lower_lat[3]), np.flipud(ra_lower_lat[2]),
            np.flipud(ra_lower_lat[1]),
            np.flipud(ra_lower_lat[0])))
        polyCont = ','.join(str(llo) + ' ' + str(lla) for llo, lla in zip(lons,
            lats))
        wkt = 'POLYGON((%s))' % polyCont

        # Change the dataset geolocation to cover all subswaths
        geoloc.geometry = WKTReader().read(wkt)
        geoloc.save()

        mm = self.__module__.split('.')
        module = '%s.%s' %(mm[0],mm[1])
        mp = media_path(module, swath_data[i].fileName)

        for i in range(n_subswaths):
            # search db for model wind field - simply take first item for
            # now...
            wind = Dataset.objects.filter(
                    source__platform__short_name = 'NCEP-GFS', 
                    time_coverage_start__lte = \
                        parse(swath_data[i].get_metadata()['time_coverage_start']) + timedelta(3),
                    time_coverage_start__gte = \
                        parse(swath_data[i].get_metadata()['time_coverage_start']) - timedelta(3)
                )[0]
            
            fdg = swath_data[i].geophysical_doppler_shift(
                    wind=nansat_filename(wind.dataseturi_set.all()[0].uri)
                )
            swath_data[i].add_band(array=fdg, parameters={
                'wkv': 'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'
            })

            filename = 'satproj_fdg_subswath_%d.png'%i
            swath_data[i].write_figure(os.path.join(mp, filename),
                    bands='fdg', clim=[-60,60], cmapName='jet')
            # Add figure to db...

            # Reproject to leaflet projection
            xlon, xlat = swath_data[i].get_corners()
            d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 1000 1000' % (
                        xlon.min(), xlat.min(), xlon.max(), xlat.max()))
            swath_data[i].reproject(d, eResampleAlg=1, tps=True)

            filename = 'fdg_subswath_%d.png'%i
            swath_data[i].write_figure(os.path.join(mp, filename),
                    bands='fdg', clim=[-60,60], cmapName='jet',
                    mask_array=swath_data[i]['swathmask'],
                    mask_lut={0:[128,128,128]}, transparency=[128,128,128])
            # change the below to using write_figure
            #nansatFigure(swath_data[i]['fdg'], swath_data[i]['swathmask'],
            #-60, 60, mp, prodName, cmapName='jet')

            # Get DatasetParameter
            dsp, created = DatasetParameter.objects.get_or_create(dataset=ds,
                    parameter = Parameter.objects.get(
                        standard_name =
                        'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'
                        ))

            # Create Visualization
            geom = GeographicLocation.objects.get_or_create(
                    geometry=WKTReader().read(swath_data[i].get_border_wkt()))[0]
            vv = Visualization(
                    uri='file://localhost%s/%s' % (mp, filename),
                    title='Geophysical Doppler shift (swath %s)' %(i+1),
                    geographic_location = geom
                )
            vv.save()

            # Create VisualizationParameter
            vp = VisualizationParameter(visualization=vv, ds_parameter=dsp)
            vp.save()

        return ds, True

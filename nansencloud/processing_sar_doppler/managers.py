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
from nansencloud.catalog.models import Dataset, DatasetURI
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
            astep[i] = max(1, lon[i].shape[0] / num_border_points)
            rstep[i] = max(1, lon[i].shape[1] / num_border_points)
            az_left_lon[i] = lon[i][0:-1:astep[i],0]
            az_left_lat[i] = lat[i][0:-1:astep[i],0]
            ra_upper_lon[i] = lon[i][-1,0:-1:rstep[i]] 
            ra_upper_lat[i] = lat[i][-1,0:-1:rstep[i]]
            az_right_lon[i] = lon[i][0:-1:astep[i],-1]
            az_right_lat[i] = lat[i][0:-1:astep[i],-1]
            ra_lower_lon[i] = lon[i][0,0:-1:rstep[i]]
            ra_lower_lat[i] = lat[i][0,0:-1:rstep[i]] 

        lons = np.concatenate((az_left_lon[0], ra_upper_lon[0][1:],
            ra_upper_lon[1][1:], ra_upper_lon[2][1:], ra_upper_lon[3][1:],
            ra_upper_lon[4][1:], az_right_lon[4][1:], ra_lower_lon[0][1:],
            ra_lower_lon[1][1:], ra_lower_lon[2][1:], ra_lower_lon[3][1:],
            ra_lower_lon[4][1:-2]))
        # apply 180 degree correction to longitude - code copied from
        # get_border_wkt...
        for ilon, lon in enumerate(lons):
            lons[ilon] = copysign(acos(cos(lon * pi / 180.)) / pi * 180,
                    sin(lon * pi / 180.))
        lats = np.concatenate((az_left_lat[0], ra_upper_lat[0][1:],
            ra_upper_lat[1][1:], ra_upper_lat[2][1:], ra_upper_lat[3][1:],
            ra_upper_lat[4][1:], az_right_lat[4][1:], ra_lower_lat[0][1:],
            ra_lower_lat[1][1:], ra_lower_lat[2][1:], ra_lower_lat[3][1:],
            ra_lower_lat[4][1:-2]))
        polyCont = ','.join(str(lon) + ' ' + str(lat) for lon, lat in zip(lons,
            lats))
        wkt = 'POLYGON((%s))' % polyCont

        import ipdb; ipdb.set_trace()

        geometry=WKTReader().read(wkt)

        # Change the geolocation to cover all subswaths
            #geolocation = GeographicLocation.objects.get_or_create(
                            #geometry=WKTReader().read(n.get_border_wkt()))[0]

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
                'wkv': 'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'})

            lon, lat = swath_data[i].get_corners()
            d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 1000 1000' % (
                        lon.min(), lat.min(), lon.max(), lat.max()))
            swath_data[i].reproject(d, eResampleAlg=1, tps=True)

            # OBS: these lines are only correct if the media_path method is run
            # from the management commad..
            mm = self.__module__.split('.')
            module = '%s.%s' %(mm[0],mm[1])
            media_path = media_path(module, swath_data[i].fileName)
            prodName = 'fdg_subswath_%d.png'%i

            # change the below to using write_figure
            nansatFigure(swath_data[i]['fdg'], swath_data[i]['swathmask'], -60, 60, media_path,
                    prodName, cmapName='jet')

            # Now add figure to db...
            uri = DatasetURI.objects.get_or_create(
                    uri='file://localhost/%s' % media_path,
                    dataset=ds)[0]
            meta = swath_data[i].bands()[swath_data[i]._get_band_number('fdg')]
            #product = Product(
            #    short_name='%s_ss%d'%(meta['short_name'], i),
            #    standard_name=meta['standard_name'],
            #    long_name=meta['long_name'],
            #    units='Hz',
            #    location=location,
            #    time=ds.time_coverage_start)

            #product.save()

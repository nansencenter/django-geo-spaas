import os
import numpy as np
import warnings

from django.conf import settings
from django.contrib.gis.geos import WKTReader

from geospaas.utils import nansat_filename, media_path, product_path
from geospaas.vocabularies.models import Parameter
from geospaas.catalog.models import DatasetParameter, GeographicLocation
from geospaas.catalog.models import Dataset, DatasetURI
from geospaas.viewer.models import Visualization
from geospaas.viewer.models import VisualizationParameter
from geospaas.nansat_ingestor.managers import DatasetManager as DM

# This should probably be done differently..
from geospaas.processing_sar_nrcs.utils import nansatFigure

from nansat.nsr import NSR
from nansat.domain import Domain
from nansat.nansat import Nansat

standard_name = 'surface_backwards_scattering_coefficient_of_radar_wave'
polarization_clims = {
        'HH': [-20, 0],
        'HV': [-30, -10],
        'VV': [-20, 0],
        'VH': [-20, 0],
    }

class DatasetManager(DM):

    def get_or_create(self, uri, reprocess=False, *args, **kwargs):
        # ingest file to db
        ds, created = super(DatasetManager, self).get_or_create(uri, *args,
                **kwargs)

        # set Dataset entry_title
        ds.entry_title = 'SAR NRCS'
        ds.save()

        # Unless reprocess==True, we may not need to do the following... (see
        # managers.py in sar doppler processor)
        #visExists = ... # check if visualization(s) already created
        #if visExists and not reprocess:
        #    warnings.warn('NO VISUALISATIONS CREATED - update managers.py')
        #    return ds, created

        n = Nansat(nansat_filename(uri))
        n.resize(pixelsize=500)
        lon, lat = n.get_corners()
        d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 1000 1000' % (
                        lon.min(), lat.min(), lon.max(), lat.max()))
        n.reproject(d, eResampleAlg=1, tps=True)

        # Get all NRCS bands
        s0bands = []
        pp = []
        for key, value in n.bands().iteritems():
            try:
                if value['standard_name']==standard_name:
                    s0bands.append(key)
                    pp.append(value['polarization'])
            except KeyError:
                continue

        ''' Create data products
        '''
        mm = self.__module__.split('.')
        module = '%s.%s' %(mm[0],mm[1])
        mp = media_path(module, n.fileName)
        ppath = product_path(module, n.fileName)

        # Create png's for each band
        num_products = 0
        swathmask = n['swathmask']

        for band in s0bands:
            meta = n.bands()[band]

            product_filename = '%s_%s.png'%(meta['short_name'],
                    meta['polarization'])

            s0 = n[band]
            mask = np.copy(swathmask)
            mask[s0 == np.nan] = 0
            mask[s0 <= 0] = 0
            s0 = np.log10(s0)*10.

            nansatFigure(s0, mask, polarization_clims[meta['polarization']][0],
                    polarization_clims[meta['polarization']][1], mp,
                    product_filename)
            

            # Get DatasetParameter
            param = Parameter.objects.get(short_name = meta['short_name'])
            dsp, created = DatasetParameter.objects.get_or_create(dataset=ds,
                    parameter = param)
    
            # Create Visualization
            geom, created = GeographicLocation.objects.get_or_create(
                    geometry=WKTReader().read(n.get_border_wkt()))
            vv, created = Visualization.objects.get_or_create(
                    uri='file://localhost%s/%s' % (mp, product_filename),
                    title='%s %s polarization' %(param.standard_name,
                        meta['polarization']),
                    geographic_location = geom
                )

            # Create VisualizationParameter
            vp, created = VisualizationParameter.objects.get_or_create(
                    visualization=vv, ds_parameter=dsp)

        return ds, True

        #    prodFileURI = os.path.join(media_path, product_filename)
        #    prodHttpURI = os.path.join(httpURIbase, product_filename)
        #    create_product(prodHttpURI, ds, meta, 'dB')
        #    num_products += 1


        #    for band in ingest_creates:
        #        filename = '%s_subswath_%d.png'%(band, i)
        #        # check uniqueness of parameter
        #        param = Parameter.objects.get(short_name = band)
        #        swath_data[i].write_figure(os.path.join(mp, filename),
        #            bands=band,
        #            mask_array=swath_data[i]['swathmask'],
        #            mask_lut={0:[128,128,128]}, transparency=[128,128,128])

        #        # Get DatasetParameter
        #        dsp, created = DatasetParameter.objects.get_or_create(dataset=ds,
        #            parameter = param)

        #        # Create Visualization
        #        geom, created = GeographicLocation.objects.get_or_create(
        #            geometry=WKTReader().read(swath_data[i].get_border_wkt()))
        #        vv, created = Visualization.objects.get_or_create(
        #            uri='file://localhost%s/%s' % (mp, filename),
        #            title='%s (swath %d)' %(param.standard_name, i+1),
        #            geographic_location = geom
        #        )

        #        # Create VisualizationParameter
        #        vp, created = VisualizationParameter.objects.get_or_create(
        #                visualization=vv, ds_parameter=dsp
        #            )

        #return ds, True


#####
        #for i in range(n_subswaths):
        #    # Add Doppler anomaly
        #    swath_data[i].add_band(array=swath_data[i].anomaly(), parameters={
        #        'wkv':
        #        'anomaly_of_surface_backwards_doppler_centroid_frequency_shift_of_radar_wave'
        #    })
        #    # search db for model wind field - simply take first item for
        #    # now...
        #    wind = Dataset.objects.filter(
        #            source__platform__short_name = 'NCEP-GFS', 
        #            time_coverage_start__lte = \
        #                parse(swath_data[i].get_metadata()['time_coverage_start']) + timedelta(3),
        #            time_coverage_start__gte = \
        #                parse(swath_data[i].get_metadata()['time_coverage_start']) - timedelta(3)
        #        )[0]
        #    bandnum = swath_data[i]._get_band_number({
        #        'standard_name': \
        #            'surface_backwards_doppler_centroid_frequency_shift_of_radar_wave',
        #        })
        #    pol = swath_data[i].get_metadata(bandID=bandnum, key='polarization')
        #    fww = swath_data[i].wind_waves_doppler(
        #            nansat_filename(wind.dataseturi_set.all()[0].uri),
        #            pol
        #        )
        #    swath_data[i].add_band(array=fww, parameters={
        #        'wkv':
        #        'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_wind_waves'
        #    })

        #    swath_data[i].add_band(array=swath_data[i].geophysical_doppler_shift(
        #        wind = nansat_filename(wind.dataseturi_set.all()[0].uri)),
        #        parameters={'wkv':
        #            'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'}
        #    )

        #    # Export data to netcdf
        #    print('Exporting %s (subswath %d)' %(swath_data[i].fileName, i))
        #    fn = os.path.join(
        #            ppath, 
        #            os.path.basename(swath_data[i].fileName).split('.')[0] 
        #                + 'subswath%d.nc'%(i)
        #        )
        #    swath_data[i].set_metadata(key='Originating file',
        #            value=swath_data[i].fileName)
        #    swath_data[i].export(fileName=fn)
        #    ncuri = os.path.join('file://localhost', fn)
        #    new_uri, created = DatasetURI.objects.get_or_create(uri=ncuri,
        #            dataset=ds)

        #    # Maybe add figures in satellite projection...
        #    #filename = 'satproj_fdg_subswath_%d.png'%i
        #    #swath_data[i].write_figure(os.path.join(mp, filename),
        #    #        bands='fdg', clim=[-60,60], cmapName='jet')
        #    ## Add figure to db...

        #    # Reproject to leaflet projection
        #    xlon, xlat = swath_data[i].get_corners()
        #    d = Domain(NSR(3857),
        #           '-lle %f %f %f %f -tr 1000 1000' % (
        #                xlon.min(), xlat.min(), xlon.max(), xlat.max()))
        #    swath_data[i].reproject(d, eResampleAlg=1, tps=True)

        #    # Visualizations of the following bands (short_names) are created
        #    # when ingesting data:
        #    ingest_creates = [
        #            'valid_doppler', 'valid_land_doppler', 'valid_sea_doppler',
        #            'dca', 'fww', 'fdg',
        #        ]
        #    # (the geophysical doppler shift must later be added in a separate
        #    # manager method in order to estimate the range bias after
        #    # processing multiple files)
        #    for band in ingest_creates:
        #        filename = '%s_subswath_%d.png'%(band, i)
        #        # check uniqueness of parameter
        #        param = Parameter.objects.get(short_name = band)
        #        swath_data[i].write_figure(os.path.join(mp, filename),
        #            bands=band,
        #            mask_array=swath_data[i]['swathmask'],
        #            mask_lut={0:[128,128,128]}, transparency=[128,128,128])

        #        # Get DatasetParameter
        #        dsp, created = DatasetParameter.objects.get_or_create(dataset=ds,
        #            parameter = param)

        #        # Create Visualization
        #        geom, created = GeographicLocation.objects.get_or_create(
        #            geometry=WKTReader().read(swath_data[i].get_border_wkt()))
        #        vv, created = Visualization.objects.get_or_create(
        #            uri='file://localhost%s/%s' % (mp, filename),
        #            title='%s (swath %d)' %(param.standard_name, i+1),
        #            geographic_location = geom
        #        )

        #        # Create VisualizationParameter
        #        vp, created = VisualizationParameter.objects.get_or_create(
        #                visualization=vv, ds_parameter=dsp
        #            )

        #return ds, True

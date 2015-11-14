import os
import time
from datetime import datetime, timedelta
import numpy as np
from xml.etree.ElementTree import XML, ElementTree, tostring

import matplotlib.pyplot as plt

import gdal
#from pyhdf import SD

from nansat import Domain, Nansat, Figure, NSR

#from boreali import Boreali


class ModisL2Image(Nansat):
    '''
    Read parameters from MERIS file
    '''

    def __init__(self, fileName, logLevel=30, cloudBits=None, debug=False, GCP_COUNT=10):
        '''
        Check if image is small or taken at night, add mask
        '''
        RasterYSize, RasterXSize, day_night_flag, mapperName = self.get_size_day_mapper(fileName)

        isday = day_night_flag == 'Day'
        isbig = (RasterXSize > 200) * (RasterYSize > 200)
        if not isday:
            print 'Night image'
            time.sleep(0.5)
            raise Exception('Night image!')

        if not isbig:
            print 'Too little image!'
            time.sleep(0.5)
            raise Exception('Too little image!')

        Nansat.__init__(self, fileName, logLevel=logLevel, mapperName=mapperName, GCP_COUNT=GCP_COUNT)

        # good bits for amazon plume studying
        if cloudBits is None:
            #cloudBits=[4, 5, 6, 10, 15, 20, 23, 30]
            # good bits for NRT
            cloudBits = [1, 6, 10, 16, 29]
            #cloudBits=[1, 4, 5, 6, 9, 10, 13, 15, 20, 21, 23, 28, 29, 30]
            # yellow sea:
            #cloudBits = [1, 4, 5, 6, 9, 10, 15, 20, 29]
            #cloudBits=[1, 4, 5, 6, 9, 10, 15, 20, 21, 29]

            # for china
            #cloudBits=[1, 5, 6, 9, 10, 13, 15, 20, 23, 28, 29, 30]

        self.add_mask(cloudBits, debug=debug)

        # replace cdom_index and sst with cdom_a and SST
        self.rename_band('cdom_index', 'cdom_a')
        self.rename_band('sst', 'SST')

    def rename_band(self, oldName, newName):
        # replace cdom_index and sst with cdom_a and SST
        bands = self.bands()
        for band in bands:
            if bands[band]['name'] == oldName:
                bandMeta = bands[band]
                bandMeta['name'] = newName
                self.get_GDALRasterBand(oldName).SetMetadata(bandMeta)


    def get_size_day_mapper(self, fileName):
        ''' Get size of the image, value of the Day flag and appropriate mapper
        based on the file extension (hdf or nc)'''

        fileExt = os.path.splitext(fileName)[1]
        if fileExt == '.nc':
            ds = gdal.Open('HDF5:"%s"://navigation_data/longitude' % fileName)
            day_night_flag = ds.GetMetadata()['day_night_flag']
            mapperName = 'obpg_l2_nc'
        else:
            ds = gdal.Open('HDF4_SDS:UNKNOWN:"%s":11' % fileName)
            day_night_flag = ds.GetMetadata()['Day or Night']
            mapperName = 'obpg_l2'

        RasterYSize, RasterXSize = ds.RasterYSize, ds.RasterXSize

        ds = None
        return RasterYSize, RasterXSize, day_night_flag, mapperName

    def add_mask(self, cloudBits, landBits=[2], debug=False):
        l2c_mask = self.l2c_mask(cloudBits, landBits, debug=debug)
        self.add_band(array=l2c_mask, parameters={'wkv':'quality_flags', 'name': 'mask'})

    def l2c_mask(self, cloudBits, landBits=[2], debug=False):
        '''Create l2c_flags:
        Flag coding:
        1 - cloud   (value = 1)
        2 - land    (value = 2)
        8 - water   (value = 64)

        L2 BITS:
        f01_name=ATMFAIL            #
        f02_name=LAND
        f03_name=PRODWARN
        f04_name=HIGLINT            #
        f05_name=HILT               #
        f06_name=HISATZEN           #
        f07_name=COASTZ
        f08_name=SPARE
        f09_name=STRAYLIGHT         .#
        f10_name=CLDICE             #
        f11_name=COCCOLITH          .
        f12_name=TURBIDW            .
        f13_name=HISOLZEN           #
        f14_name=SPARE
        f15_name=LOWLW              #
        f16_name=CHLFAIL
        f17_name=NAVWARN
        f18_name=ABSAER
        f19_name=SPARE
        f20_name=MAXAERITER         #
        f21_name=MODGLINT           .#
        f22_name=CHLWARN
        f23_name=ATMWARN            #
        f24_name=SPARE
        f25_name=SEAICE
        f26_name=NAVFAIL
        f27_name=FILTER
        f28_name=SSTWARN            .
        f29_name=SSTFAIL            #
        f30_name=HIPOL              #
        f31_name=PRODFAIL           .
        f32_name=SPARE
        '''

        if os.path.splitext(self.fileName)[1] == '.nc':
            l2_flags = self['l2_flags']
        else:
            l2_flags = self['flags']

        # == FOR DEBUG ==
        #import matplotlib.pyplot as plt
        #plt.imshow(l2_flags);plt.colorbar();plt.show()
        #chlor_a = self['chlor_a']
        #plt.imsave(self.name + 'chlor_a.png', chlor_a, vmin=-2, vmax=2)
        if debug:
            for bit in range(0, 32):
                maskTmp = np.bitwise_and(l2_flags, np.power(np.uint32(2), bit))
                fName = '%s_%02d.png' % (self.name, bit)
                print fName
                plt.imsave(fName, maskTmp)


        # create l2c_falg matrix with water bit by default
        l2c_mask = 64 * np.ones(l2_flags.shape, np.uint8)

        # get solar zenith and mask values below horizon
        #sd = SD.SD(self.fileName)
        #csol_z = a.select('csol_z')[:]
        #l2c_mask[csol_z >= 90] = 0

        # process cloud and land masks
        maskLand = np.zeros(l2c_mask.shape)
        maskCloud = np.zeros(l2c_mask.shape)
        # check every bit in a set
        for bit in landBits:
            maskTmp = np.bitwise_and(l2_flags, np.power(np.uint32(2), bit-1))
            maskLand[maskTmp > 0] = 1
        # check every bit in a set
        for bit in cloudBits:
            maskTmp = np.bitwise_and(l2_flags, np.power(np.uint32(2), bit-1))
            maskCloud[maskTmp > 0] = 1

        # set cloud bit
        l2c_mask[maskCloud > 0] = 1
        # set land bitm
        l2c_mask[maskLand > 0] = 2

        return l2c_mask

    def process_std(self, settings):
        '''Standard L2-processing: only preview generation'''
        oBaseFileName = os.path.split(self.fileName)[1]
        rgbName = os.path.join(settings['output_directory'], oBaseFileName + '_rgb.png')
        sstName = os.path.join(settings['output_directory'], oBaseFileName + '_sst.png')
        chlName = os.path.join(settings['output_directory'], oBaseFileName + '_chl.png')

        if not os.path.exists(settings['output_directory']):
            os.makedirs(settings['output_directory'])

        lon, lat = self.get_corners()
        d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 5000 5000' % (
                                lon.min(), lat.min(), lon.max(), lat.max()))
        self.reproject(d)

        # good bits for NRT
        mask = self['mask']

        productMetadata = []
        # generate RGB quicklook
        if not os.path.exists(rgbName):
            self.write_figure(rgbName, ['Rrs_678', 'Rrs_555', 'Rrs_443'],
                            clim=[[0,0,0],[0.02, 0.025, 0.016]],
                            mask_array=mask,
                            mask_lut={0:[128,128,128],
                                      1:[128,128,128],
                                      2:[128,128,128]},
                            transparency=[128,128,128])
        productMetadata.append(dict(
            uri = rgbName,
            short_name = 'rgb',
            standard_name = 'rgb',
            long_name='RGB',
            units='',
            ))

        # generate SST quicklook
        if not os.path.exists(sstName):
            try:
                self.write_figure(sstName, 'SST',
                            clim=[-5, 20],
                            mask_array=mask,
                            mask_lut={0:[128,128,128],
                                      1:[128,128,128],
                                      2:[128,128,128]},
                            transparency=[128,128,128])
            except:
                self.logger.error('No SST in %s' % self.name)
        bandMeta = self.bands()[self._get_band_number('SST')]
        productMetadata.append(dict(
            uri = sstName,
            short_name = 'SST',
            standard_name = bandMeta['standard_name'],
            long_name = bandMeta['long_name'],
            units = bandMeta['units'],
            ))

        # generate image with flags
        if not os.path.exists(chlName):
            try:
                self.write_figure(chlName, 'chlor_a',
                            clim=[0, 5],
                            logarithm=True,
                            mask_array=mask,
                            mask_lut={0:[128,128,128],
                                      1:[128,128,128],
                                      2:[128,128,128]},
                            transparency=[128,128,128])
            except:
                self.logger.error('No chlor_a in %s' % self.name)

        bandMeta = self.bands()[self._get_band_number('chlor_a')]
        productMetadata.append(dict(
            uri = chlName,
            short_name = 'chlor_a',
            standard_name = bandMeta['standard_name'],
            long_name = bandMeta['long_name'],
            units = bandMeta['units'],
            ))

        return productMetadata

    def process_boreali(self, opts):
        '''Advanced processing of MODIS images:
        retrieve chl, tsm, doc with boreali
        generate images
        '''

        pnDefaults = {
            'lmchl': [0, 5, False],
            'lmtsm': [0, 3, False],
            'lmdoc': [0, 2, False],
            'lmmse': [1e-8, 1e-5, True]}

        borMinMax = [[pnDefaults['lmchl'][0], pnDefaults['lmchl'][1]],
                     [pnDefaults['lmtsm'][0], pnDefaults['lmtsm'][1]],
                     [pnDefaults['lmdoc'][0], pnDefaults['lmdoc'][1]]]

        dtsDomain = Domain(opts['srs'], opts['ext'])

        fileName = self.get_metadata('name')
        oBaseFileName = self.get_metadata('name').strip('"').strip("'")
        ncName = opts['oDir'] + oBaseFileName + '.nc'
        print ncName
        prodFileNames = {}
        for pn in opts['prods']:
            prodFileNames[pn] = '%s/%s.%s.png' % (opts['oDir'], oBaseFileName, pn)

        if os.path.exists(ncName):
            print '%s already exist!' % ncName
        else:
            # good bits for NRT
            #self.add_mask(cloudBits=[1, 4, 5, 6, 9, 10, 13, 15, 20, 21, 23, 28, 29, 30])

            try:
                self.reproject(dtsDomain)
            except:
                print 'Cannot reproject %s. Skipping' % fileName
                return 1
            else:
                Rrsw_412 = self['Rrsw_412']
                if Rrsw_412 is None:
                    return 1
                # process input with BOREALI
                b = Boreali(model='northsea', zone='northsea')
                cImg = b.process_lm(self, wavelen=[412, 443, 488, 531, 555, 667],
                                          start=opts['start'],
                                          minmax=borMinMax)

                # generate Nansat with results
                img2 = Nansat(domain=self)
                for i, pn in enumerate(opts['prods']):
                    img2.add_band(array=cImg[i, :, :], parameters={'name': pn})
                img2.add_band(array=self['mask'], parameters={'name': 'mask'})

                # export results into NC-file
                img2.export(ncName)

                # write images with concentrations
                for pn in opts['prods']:
                    pnd = pnDefaults[pn]
                    img2.write_figure(prodFileNames[pn], pn, clim=[pnd[0], pnd[1]], legend=True, logarithm=pnd[2])

        return 0

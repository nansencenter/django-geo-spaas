from optparse import make_option

from nansat.tools import GeolocationError

from django.core.management.base import BaseCommand

from nansencloud.utils import uris_from_args
from nansencloud.catalog.models import DatasetURI
from nansencloud.processing_sar_nrcs.models import Dataset

class Command(BaseCommand):
    args = '<filename>'
    help = '''
        Add SAR data to catalog archive and make png images with NRCS for
        display in Leaflet
    '''

    def add_arguments(self, parser):
        parser.add_argument('--reprocess', action='store_true', 
                help='Force reprocessing')

    def handle(self, *args, **options):
        #if not len(args)==1:
        #    raise IOError('Please provide one filename only')

        for non_ingested_uri in uris_from_args(*args):
            self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
            try:
                ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **options)
            except GeolocationError:
                self.stdout.write('Geolocation error in: %s\n' % non_ingested_uri)
                continue
            if cr:
                self.stdout.write('Successfully added: %s\n' % non_ingested_uri)
            else:
                self.stdout.write('Was already added: %s\n' % non_ingested_uri)







    # The following is replaced in managers.py, except the quad-pol part
    #def process(self, ds):
    #    ''' Create quicklooks of all NRCS bands.

    #    TODO: major cleanup + move code out of nansencloud into a general SAR
    #    processing package
    #    '''
    #    clims = {
    #        'HH': [-20, 0],
    #        'HV': [-30, -10],
    #        'VV': [-20, 0],
    #        'VH': [-20, 0],
    #    }
    #    dsURI = ds.datalocation_set.filter(
    #            protocol=DataLocation.LOCALFILE)[0].uri

    #    qp = False
    #    try:
    #        n = QuadPol(dsURI, wind_direction='ncep_wind_online')
    #        qp = True
    #    except:
    #        n = Nansat(dsURI)

    #    # Get all NRCS bands
    #    s0bands = []
    #    pp = []
    #    for key, value in n.bands().iteritems():
    #        try:
    #            if value['standard_name']==standard_name:
    #                s0bands.append(key)
    #                pp.append(value['polarization'])
    #        except KeyError:
    #            continue

    #    if qp:
    #        for i, band in enumerate(s0bands):
    #            s0bands[i] = band+'_reduced'

    #    media_path = vtools.media_path(self.__module__,
    #            os.path.split(n.fileName)[-1].split('.')[0])

    #    if qp:
    #        n.export(os.path.join(media_path, prodBaseName+'.nc'))

    #    lon, lat = n.get_corners()
    #    d = Domain(NSR(3857),
    #               '-lle %f %f %f %f -tr 1000 1000' % (
    #                    lon.min(), lat.min(), lon.max(), lat.max()))
    #    n.reproject(d, eResampleAlg=1, tps=True)

    #    # Create png's for each band
    #    num_products = 0
    #    swathmask = n['swathmask']
    #    httpURIbase = os.path.join(settings.MEDIA_URL,
    #                self.__module__.split('.')[0],
    #                self.__module__.split('.')[1], prodBaseName)
    #    for band in s0bands:
    #        meta = n.bands()[band]
    #        product_filename = '%s_%s.png'%(meta['short_name'],
    #                meta['polarization'])

    #        s0 = n[band]
    #        mask = np.copy(swathmask)
    #        mask[s0 == np.nan] = 0
    #        mask[s0 <= 0] = 0
    #        s0 = np.log10(s0)*10.

    #        nansatFigure(s0, mask, min, max, media_path,
    #                product_filename)

    #        prodFileURI = os.path.join(media_path, product_filename)
    #        prodHttpURI = os.path.join(httpURIbase, product_filename)
    #        create_product(prodHttpURI, ds, meta, 'dB')
    #        num_products += 1

    #    if qp:
    #        print('Make PR image...')
    #        pname = make_PR_image(n, dir=media_path)
    #        prodFileURI = os.path.join(media_path, pname)
    #        prodHttpURI = os.path.join(httpURIbase, pname)
    #        create_product(prodHttpURI, ds, n.bands()['PR'], 'm/m')
    #        num_products += 1

    #        print('Make PD image...')
    #        pname = make_PD_image(n, dir=media_path)
    #        prodFileURI = os.path.join(media_path, pname)
    #        prodHttpURI = os.path.join(httpURIbase, pname)
    #        create_product(prodHttpURI, ds, n.bands()['PD'], 'm/m')
    #        num_products += 1

    #        try:
    #            print('Make NP image...')
    #            pname = make_NP_image(n, dir=media_path)
    #            prodFileURI = os.path.join(media_path, pname)
    #            prodHttpURI = os.path.join(httpURIbase, pname)
    #            create_product(prodHttpURI, ds, n.bands()['PD'], 'm/m')
    #            num_products += 1
    #        except Exception as e:
    #            print e
    #        print('Make CP image...')
    #        pname = make_NRCS_image(n, 'CP', dir=media_path)
    #        prodFileURI = os.path.join(media_path, pname)
    #        prodHttpURI = os.path.join(httpURIbase, pname)
    #        create_product(prodHttpURI, ds, n.bands()['PD'], 'm/m')
    #        num_products += 1


    #    return num_products

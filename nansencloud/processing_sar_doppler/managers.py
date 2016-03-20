import os
from dateutil.parser import parse
from datetime import timedelta

from django.conf import settings
from django.db import models

from nansencloud.utils import nansat_filename
from nansencloud.vocabularies.models import Parameter
from nansencloud.catalog.models import Dataset, DatasetURI
from nansencloud.nansat_ingestor.managers import DatasetManager as DM

from nansencloud.processing_sar.tools import nansatFigure

from nansencloud.viewer import tools as vtools

from nansat.nsr import NSR
from nansat.domain import Domain
from sardoppler.sardoppler import Doppler


class DatasetManager(DM):

    def get_or_create(self, uri, *args, **kwargs):
        # ingest file to db
        super(DatasetManager, self).get_or_create(uri, *args, **kwargs)

        fn = nansat_filename(uri)
        for i in range(5):
            # Process subswaths 
            n = Doppler(fn, subswath=i)

            # search db for model wind field - simply take first item for
            # now...
            wind = Dataset.objects.filter(
                    source__platform__short_name = 'NCEP-GFS', 
                    time_coverage_start__lte = \
                        parse(n.get_metadata()['time_coverage_start']) + timedelta(3),
                    time_coverage_start__gte = \
                        parse(n.get_metadata()['time_coverage_start']) - timedelta(3)
                )[0]
            
            fdg = n.geophysical_doppler_shift(
                    wind=nansat_filename(wind.dataseturi_set.all()[0].uri)
                )
            n.add_band(array=fdg, parameters={
                'wkv': 'surface_backwards_doppler_frequency_shift_of_radar_wave_due_to_surface_velocity'})

            lon, lat = n.get_corners()
            d = Domain(NSR(3857),
                   '-lle %f %f %f %f -tr 1000 1000' % (
                        lon.min(), lat.min(), lon.max(), lat.max()))
            n.reproject(d, eResampleAlg=1, tps=True)

            # OBS: these lines are only correct if the media_path method is run
            # from the management commad..
            mm = self.__module__.split('.')
            import ipdb
            ipdb.set_trace()
            module = '%s.%s' %(mm[0],mm[1])
            media_path = vtools.media_path(module, n.fileName)
            prodName = 'rvl_ss%d.png'%i
            prodBaseName = os.path.basename(n.fileName).split('.')[0]

            # change the below to using write_figure
            nansatFigure(n['fdg'], n['swathmask'], -60, 60, media_path,
                    prodName, cmapName='jet')

            # Now add figure to db...
            ds = Dataset.objects.get(datalocation__uri=n.fileName)
            httpURIbase = os.path.join(settings.MEDIA_URL,
                    module.split('.')[0], module.split('.')[1], prodBaseName)
            prodHttpURI = '%s/%s'%(httpURIbase, prodName)
            location = DataLocation.objects.get_or_create(protocol='HTTP',
                    uri=prodHttpURI,
                    dataset=ds)[0]
            meta = n.bands()[n._get_band_number('fdg')]
            product = Product(
                short_name='%s_ss%d'%(meta['short_name'], i),
                standard_name=meta['standard_name'],
                long_name=meta['long_name'],
                units='Hz',
                location=location,
                time=ds.time_coverage_start)

            product.save()

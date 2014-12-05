import os
import numpy as np

from django.conf import settings
from django.contrib.gis.db import models

from nansat.domain import Domain
from nansat.figure import Figure
from cat.models import Image, ImageManager, BadSourceFileError, Status,\
        Search, SourceFile


class ProcImage(Image):
    ''' Parent of all Image-like classes in proc '''
    image = models.ForeignKey(Image,
                            parent_link=True,
                            related_name='%(app_label)s_%(class)s_related')
    # dynamic related_name as explained here:
    # https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    objects = ImageManager()

    class Meta:
        abstract = True

    @classmethod
    def create(cls, image_or_filename):
        ''' Create ProcImage child from existing Image or from filename

        Parameters
        ----------
            cls : model from proc
                MerisWeb or RadarsatWeb or other similar
            image_or_filename : Image or str or unicode
                if :model:`cat.Image` :
                    the object is created and obj.image is assigned
                if str or unicode:
                    first instance of :model:`cat.Image` is
                    created and saved; then the object is created
        Returns
        -------
            obj : type(cls)
                Instance of the class that was used with create
                e.g. :model:`proc.MerisWeb`
            create : bool
                True, if the object created. False, if fetched from database

        '''

        if type(image_or_filename) == Image:

            try:
                # get Image from database
                create = False
                obj = cls.objects.get(image_id=image_or_filename.id)
            except cls.DoesNotExist:
                # create Image and save
                create = True
                obj = cls(image_id = image_or_filename.id)
                obj.__dict__.update(image_or_filename.__dict__)

        elif type(image_or_filename) in [str, unicode]:
            image = Image.objects.get_or_create(image_or_filename)[0]
            obj, create = cls.create(image)
        else:
            raise Exception('Input should be Image or filename')

        return obj, create

class Chain(models.Model):
    ''' List of processing chains'''
    name = models.CharField(max_length=100, unique=True)
    webname = models.CharField(max_length=100)
    description = models.TextField()

    def __unicode__(self):
        return '%s' % self.webname


class ProcSearch(Search):
    ''' Subcalss of cat.Search with reference to Chain '''
    chain = models.ForeignKey(Chain, blank=True, null=True, related_name='procsearches')


class MerisWeb(ProcImage):
    ''' List of images processed with the MerisWeb chain'''
    resolution = models.CharField(max_length=2)     # Spatial resolution
    level = models.CharField(max_length=1)          # Level of processing
    quicklook = models.ForeignKey(SourceFile, related_name='merisweb_imgs', blank=True, null=True)      # file with quicklook
    daily = models.BooleanField(default=False)                   # was used in daily processing
    chain = models.ForeignKey(Chain, related_name='merisweb_imgs', blank=True, null=True)

    # this is not instance specific, but a single chain for the entire model
    @classmethod
    def get_chain(cls):
        '''Define chain name and description'''
        ch = Chain.objects.get_or_create(
            name='MerisWeb',
            webname='MERIS',
            description = '''
            Simple processing of MERIS inluding only quick look production
            '''
            )[0]
        return ch

    def __unicode__(self):
        return '%s|%s|%s' % (self.sourcefile.name, self.resolution, self.level)

    def process(self, opts=None, force=False):
        '''L2-processing of MERIS images for WEB'''
        # bad files should not be attempted to be processed
        if self.image.status.status==Status.BAD_STATUS:
            raise BadSourceFileError('Cannot process %s' % str(self.sourcefile))

        if opts is None:
            opts = {
                'url': 'http://web.nersc.no/project/maires/catalog/meris/',
                'odir': '/WebData/maires.nersc.no/public_html/catalog/meris/',
                    }

        # generate quicklook
        qlName = os.path.join(opts['odir'], self.sourcefile.name) + '_.jpg'
        urlName = os.path.join(opts['url'], self.sourcefile.name) + '_.jpg'
        n = self.get_nansat()
        n.resize(width=300)
        print 'Generate %s ' % qlName
        f = n.write_figure(qlName, [7, 5, 1], clim=[[5,10,25], [35, 55, 80]])

        # set all fields
        self.quicklook = SourceFile.objects.get_or_create(urlName, force=True)[0]
        self.resolution = self.sourcefile.name.replace('__', '_').split('_')[1][0:2]
        self.level = self.sourcefile.name.replace('__', '_').split('_')[2][0]
        self.chain = MerisWeb.get_chain()

        if os.path.exists(qlName):
            return 0
        else:
            return 1

class Polarization(models.Model):
    pol = models.CharField(max_length=2)

    def __unicode__(self):
        return self.pol

class SARWeb(ProcImage):

    polarizations = models.ManyToManyField(Polarization, blank=True, null=True)
    quicklooks = models.ManyToManyField(SourceFile, related_name="sar_web", blank=True, null=True)
    chain = models.ForeignKey(Chain, related_name="sar_web")

    @classmethod
    def get_chain(cls):
        '''Define chain name and description'''
        ch = Chain.objects.get_or_create(
            name='SARWeb',
            webname='SAR',
            description = '''
                Simple processing of SAR data including quicklook production
                of calibrated NRCS
            '''
            )[0]
        return ch

    def get_ql_list(self):
        pp = [ p.pol for p in self.polarizations.all() ]
        qlname = [ ql.name for ql in self.quicklooks.all() ]
        if not qlname or not pp or len(pp)!=len(qlname):
            return []
        list = []
        for i in range(len(pp)):
            list.append((pp[i], qlname[i]))
        return list

    def get_bounds(self):
        # fetch data from DB
        coords = self.border.coords[0]
        # create list with longitudes
        lons = [lon for lon, lat in self.border.coords[0]]
        # create list with latitudes
        lats = [lat for lon, lat in self.border.coords[0]]
        return [[np.min(lats), np.min(lons)], [np.max(lats), np.max(lons)]]

    def process(self, *args, **kwargs):
        force = kwargs.pop('force', False)
        if self.image.status.status==Status.BAD_STATUS:
            raise BadSourceFileError('Cannot process %s' % str(self.filename))

        self.chain = SARWeb.get_chain()
        # Save model to be able to add polarizations
        self.save()

        n = self.get_nansat()
        n.resize(pixelsize=500)
        mask = np.ones(n.shape())
        n.add_band(array=mask,parameters={
                        'name': 'mask',
        })
        lons, lats = n.get_corners()
        srsString = '+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs'
        extentString = '-lle %f %f %f %f -tr 0.005 0.005'% (min(lons), min(lats),
                            max(lons), max(lats))
        d = Domain(srs=srsString, ext=extentString)
        n.reproject(d, eResampleAlg=2)

        try:
            savedir = kwargs.pop('savedir')
        except KeyError:
            sar_web_dir = os.path.join(settings.STATIC_ROOT, 'sar_web')
            if not os.path.isdir(sar_web_dir):
                os.mkdir(sar_web_dir)
            # could also use satellite metadata but mapper name is more generic
            # and DRY:
            savedir = os.path.join(sar_web_dir, n.mapper)

        try:
            base_url = kwargs.pop('url')
        except KeyError:
            base_url = os.path.join(settings.STATIC_URL, 'sar_web/')

        basename = os.path.basename(n.fileName).split('.')[0]

        if not os.path.isdir(savedir):
            os.mkdir(savedir)

        # color limits for various polarizations
        cLims = {'HH': [-20, 0],
                 'HV': [-30, -10],
                 'VV': [-20, 0],
                 'VH': [-20, 0],
                }

        mask = n['mask']
        for i in range(len(n.bands())):
            if n.bands()[i+1].has_key('short_name') and 'sigma0' in n.bands()[i+1]['short_name']:
                self.polarizations.add(Polarization.objects.get(
                    pol=n.bands()[i+1]['polarization']) )
                # Create quicklooks if they don't already exist
                pol = n.bands()[i+1]['polarization']
                qlname = basename+'_' + pol + '.png'
                fn = os.path.join(savedir, qlname)
                url = os.path.join(base_url, qlname)
                if not os.path.isfile(fn) or force:
                    s0lin = n[i+1]
                    s0 = np.log10(s0lin)*10.
                    maskTmp = np.array(mask)
                    maskTmp[s0 == s0[0,0]] = 0
                    f = Figure(s0)
                    f.process(cmin=cLims[pol][0],
                              cmax=cLims[pol][1],
                              cmapName='gray',
                              mask_array=maskTmp,
                              mask_lut={0:[255,0,0]})
                    # Ref nansat #98 to get a separate colorbar
                    f.save(fn, transparency=[255,0,0])

                # Add quicklook to db
                sf = SourceFile.objects.get_or_create(url, force=True)[0]
                self.quicklooks.add(sf)

        # Should we also export the calibrated SAR data to netcdf?

        return 0


##class OldAsarDopplerWeb(): ??
#
##class SarWindWeb():
#
##class SarDopplerWeb(): # only new Sentinel-1 style Doppler or also old style?
#


from django.db import models
from django.contrib.gis.db import models as geomodels

from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import Dataset as CatalogDataset


class Search(geomodels.Model):
    ''' Search parameters '''
    sdate = geomodels.DateTimeField(blank=True, null=True) # when was search
    date0 = geomodels.DateField()                          # from this date
    date1 = geomodels.DateField()                          # until this date
    source = geomodels.ForeignKey(CatalogSource, blank=True, null=True)

    # GeoDjango-specific: a geometry field (PolygonField), and
    # overriding the default manager with a GeoManager instance.
    polygon = geomodels.PolygonField(blank=True, null=True) # intersect this poly
    objects = geomodels.GeoManager()

    def __str__(self):
        poly = ''
        if self.polygon is not None:
            poly = str(self.polygon.num_points)

        return self.sdate.strftime('%Y-%m-%d %H:%M ') + poly


class Dataset(CatalogDataset):
    class Meta:
        proxy = True

    # TODO: return javascript string according to geometry type
    def geo_js(self):
        return "L.polygon( %s, {color: '#fff', weight: 1, fillOpacity: 0.05, fillColor: '#f00'});" %self.border2str()

    def const_geo_js(self):
        return "L.polygon( %s, {color: '#fff', weight: 0.5, fillOpacity: 0, fillColor: '#b20000'});" %self.border2str()

    def border2str(self):
        ''' Generate Leaflet JavaScript defining the border polygon'''
        borderStr = '['
        for coord in self.geolocation.geometry.coords[0]:
            borderStr += '[%f, %f],' % coord[::-1]
        borderStr += "]"
        return borderStr


    def products(self):
        ''' Return list of all associated products '''
        httpDataLocations = self.datalocation_set.filter(protocol='HTTP')
        products = [hdl.product_set.all()[0] for hdl in httpDataLocations]
        return products

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

    def border2str(self):
        ''' Generate Leaflet JavaScript defining the border polygon'''
        borderStr = '['
        for coord in self.geolocation.geometry.coords[0]:
            borderStr += '[%f, %f],' % coord[::-1]
        borderStr += "]"
        return borderStr


import os

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.gis.db import models as geomodels

from nansencloud.catalog.models import GeographicLocation
from nansencloud.catalog.models import Source as CatalogSource
from nansencloud.catalog.models import Dataset as CatalogDataset
from nansencloud.catalog.models import DatasetParameter as CatalogDatasetParameter

class Search(geomodels.Model):
    ''' Search parameters '''
    sdate = models.DateTimeField() # when was search
    date0 = models.DateField()
    date1 = models.DateField()
    source = models.ForeignKey(CatalogSource, blank=True, null=True)

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

    jsPolygonTemplate = "L.polygon( %s, {color: '#fff', weight: %f, fillOpacity: %f, fillColor: '%s'});"
    jsPointTemplate = "L.marker([%f, %f]);"

    def geo_js_generic(self, weight, fillOpacity, fillColor, **kwargs):
        if self.geographic_location.geometry.geom_type == 'Polygon':
            jscode = self.jsPolygonTemplate % (self.border2str(), weight, fillOpacity, fillColor)
        elif self.geographic_location.geometry.geom_type == 'Point':
            jscode = self.jsPointTemplate % (self.geographic_location.geometry.coords[1],
                                            self.geographic_location.geometry.coords[0])
        return jscode


    def geo_js(self):
        return self.geo_js_generic(1, 0.05, '#f00')

    def const_geo_js(self):
        return self.geo_js_generic(0.5, 0, '#b20000')

    def border2str(self):
        ''' Generate Leaflet JavaScript defining the border polygon'''
        borderStr = '['
        for coord in self.geographic_location.geometry.coords[0]:
            borderStr += '[%f, %f],' % coord[::-1]
        borderStr += "]"
        return borderStr

    def visualizations(self):
        ''' Return list of all associated visualizations '''
        return Visualization.objects.filter(
            ds_parameters__dataset=self).distinct()

class VisualizationParameter(models.Model):
    visualization = models.ForeignKey('Visualization', on_delete=models.CASCADE)
    ds_parameter = models.ForeignKey(CatalogDatasetParameter, on_delete=models.CASCADE)

    def __str__(self):
        return self.ds_parameter.__str__()

class Visualization(models.Model):

    uri = models.URLField()
    # A visualization may contain more than one parameter, and the same
    # parameter can be visualized in many ways..
    ds_parameters = models.ManyToManyField(CatalogDatasetParameter,
            through=VisualizationParameter)
    title = models.CharField(max_length=50, default='')
    geographic_location = models.ForeignKey(GeographicLocation, blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return os.path.join(settings.MEDIA_URL,
                self.uri.split(settings.MEDIA_URL)[1])



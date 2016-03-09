from django.db import models
from django.utils import timezone
from django.contrib.gis.db import models as geomodels

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

    # TODO: return javascript string according to geometry type
    def geo_js(self):
        return "L.polygon( %s, {color: '#fff', weight: 1, fillOpacity: 0.05, fillColor: '#f00'});" %self.border2str()

    def const_geo_js(self):
        return "L.polygon( %s, {color: '#fff', weight: 0.5, fillOpacity: 0, fillColor: '#b20000'});" %self.border2str()

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

    def __str__(self):
        return self.title

    #def get_absolute_url(self):



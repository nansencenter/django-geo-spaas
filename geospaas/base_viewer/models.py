from django.db import models
from django.contrib.gis.db import models as geomodels

class SearchModelForLeaflet(geomodels.Model):
    ''' Search the datasets based with the leaflet by this model '''
    # GeoDjango-specific: a geometry field (PolygonField), and
    # overriding the default manager with a GeoManager instance.
    polygon = geomodels.PolygonField(blank=True, null=True) # intersect this poly

#class Search_with_para(Search):
#    ''' Search parameters is added '''
    #DatasetParameter = models.ForeignKey(CatalogDatasetParameter, on_delete=models.CASCADE)
#    DatasetParameter = models.ManyToManyField(CatalogDatasetParameter, blank=True)

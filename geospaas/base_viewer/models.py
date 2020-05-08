from django.db import models
from django.contrib.gis.db import models as geomodels
from geospaas.catalog.models import Source as CatalogSource
from geospaas.catalog.models import DatasetParameter as CatalogDatasetParameter
# Create your models here.
class Search(geomodels.Model):
    ''' Search without parameters '''
    sdate = models.DateTimeField() # when was search
    date0 = models.DateField()
    date1 = models.DateField()
    source = models.ManyToManyField(CatalogSource, blank=True)#, null=True)

    # GeoDjango-specific: a geometry field (PolygonField), and
    # overriding the default manager with a GeoManager instance.
    polygon = geomodels.PolygonField(blank=True, null=True) # intersect this poly

class Search_with_para(Search):
    ''' Search parameters is added '''
    #DatasetParameter = models.ForeignKey(CatalogDatasetParameter, on_delete=models.CASCADE)
    DatasetParameter = models.ManyToManyField(CatalogDatasetParameter, blank=True)

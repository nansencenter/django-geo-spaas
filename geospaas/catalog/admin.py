from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin
from geospaas.catalog.models import GeographicLocation, Source, Dataset, DatasetURI, \
        Parameter, DatasetRelationship

admin.site.register(GeographicLocation, LeafletGeoAdmin)

admin.site.register(Source, admin.ModelAdmin)
admin.site.register(Dataset, admin.ModelAdmin)
admin.site.register(DatasetURI, admin.ModelAdmin)
admin.site.register(Parameter, admin.ModelAdmin)
admin.site.register(DatasetRelationship, admin.ModelAdmin)

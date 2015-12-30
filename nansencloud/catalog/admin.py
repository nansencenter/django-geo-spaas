from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin
from models import GeographicLocation, Source, Dataset, DatasetLocation, \
        Parameter, DatasetRelationship

admin.site.register(GeographicLocation, LeafletGeoAdmin)

admin.site.register(Source, admin.ModelAdmin)
admin.site.register(Dataset, admin.ModelAdmin)
admin.site.register(DatasetLocation, admin.ModelAdmin)
admin.site.register(Parameter, admin.ModelAdmin)
admin.site.register(DatasetRelationship, admin.ModelAdmin)

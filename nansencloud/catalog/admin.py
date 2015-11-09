from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin
from models import GeographicLocation, Source, Dataset, DataLocation, Product, DatasetRelationship

admin.site.register(GeographicLocation, LeafletGeoAdmin)

admin.site.register(Source, admin.ModelAdmin)
admin.site.register(Dataset, admin.ModelAdmin)
admin.site.register(DataLocation, admin.ModelAdmin)
admin.site.register(Product, admin.ModelAdmin)
admin.site.register(DatasetRelationship, admin.ModelAdmin)

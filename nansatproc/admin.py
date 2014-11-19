# Register your models here.
from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from models import * #ProcSearch, Chain, MerisWeb, Radarsat2Web

admin.site.register(Chain, admin.ModelAdmin)
admin.site.register(ProcSearch, LeafletGeoAdmin)
admin.site.register(MerisWeb, LeafletGeoAdmin)
#admin.site.register(Radarsat2Web, LeafletGeoAdmin)

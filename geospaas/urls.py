from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

app_name = 'geospaas'
urlpatterns = [
    # Examples:
    url(r'^', include('geospaas.viewer.urls')),
    url(r'^icedrift/', include('geospaas.processing_sar_icedrift.urls')),
]

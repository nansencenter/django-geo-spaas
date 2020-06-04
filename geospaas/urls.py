from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

app_name = 'geospaas'
urlpatterns = [
    # Examples:
    #
    #url(r'adas/', include('geospaas.adas_viewer.urls')),
    url(r'^', include('geospaas.base_viewer.urls')),
]

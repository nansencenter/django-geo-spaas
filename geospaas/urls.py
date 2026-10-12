from django.urls import include, re_path

from django.contrib import admin
admin.autodiscover()

app_name = 'geospaas'
urlpatterns = [
    # Examples:
    #
    #re_path(r'adas/', include('geospaas.adas_viewer.urls')),
    re_path(r'^', include('geospaas.base_viewer.urls')),
]

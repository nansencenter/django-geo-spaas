from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

app_name = 'geospaas'
urlpatterns = [
    # Examples:
    url(r'^', include('geospaas.viewer.urls')),
]

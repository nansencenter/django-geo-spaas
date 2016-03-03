from django.conf.urls import url

from nansencloud.viewer.views import SearchDatasets, DisplayForm
from nansencloud.viewer.views import DatasetsShow

urlpatterns = [
    url(r'^$', DatasetsShow.as_view(), name='index'),
    url(r'^display/$', DisplayForm.as_view(), name='display_form'),
    url(r'^search/$', SearchDatasets.as_view(), name='search'),
]

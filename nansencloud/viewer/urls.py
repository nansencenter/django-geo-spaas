from django.conf.urls import url

from nansencloud.viewer.views import SearchDatasets, DisplayForm
from nansencloud.viewer.views import DatasetsShow

urlpatterns = [
    url(r'^$', DisplayDatasets.as_view(), name='index'),
    #url(r'^display/$', DisplayDatasets.as_view(), name='display'),
    #url(r'^search/$', SearchDatasets.as_view(), name='search'),
]

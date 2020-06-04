from django.conf.urls import url, include

from geospaas.base_viewer.views import IndexView


app_name = 'base_viewer'
urlpatterns = [
    url('', IndexView.as_view(), name='index'),
]

from django.conf.urls import url

from geospaas.base_viewer.views import IndexView

app_name = 'base_viewer'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
]

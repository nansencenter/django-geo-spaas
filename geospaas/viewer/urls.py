from django.conf.urls import url

from geospaas.viewer.views import IndexView

app_name = 'viewer'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
]

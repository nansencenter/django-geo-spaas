from django.conf.urls import url

from geospaas.viewer.views import IndexView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

]

from django.conf.urls import url

from nansencloud.viewer.views import IndexView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

]

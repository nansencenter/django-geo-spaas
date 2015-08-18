from django.conf.urls import url

from cat.views import image, band, IndexView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<image_id>\d+)/$', image, name='image'),
    url(r'^(?P<image_id>\d+)/(?P<bandName>\d+)/$', band, name='band'),

]

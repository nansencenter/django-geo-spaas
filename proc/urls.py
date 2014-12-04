from django.conf.urls import url

import nansatcat.views
import nansatproc.views

urlpatterns = [
    url(r'^$', nansatproc.views.ProcIndexView.as_view(), name='proc_index'),
    url(r'^(?P<image_id>\d+)/$', nansatcat.views.image, name='image'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/$', nansatproc.views.proc_image, name='proc_image'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/(?P<bandName>\d+)/$', nansatcat.views.band, name='band'),

    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/matchup/$', nansatproc.views.matchup, name='band'),

]

from django.conf.urls import url

import cat.views
import proc.views

urlpatterns = [
    url(r'^$', proc.views.ProcIndexView.as_view(), name='proc_index'),
    url(r'^(?P<image_id>\d+)/$', cat.views.image, name='image'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/$', proc.views.proc_image, name='proc_image'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/(?P<bandName>\d+)/$', cat.views.band, name='band'),

    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/matchup/$', proc.views.matchup, name='band'),

]

from django.conf.urls import url

import nansencloud.cat.views
import nansencloud.proc.views

urlpatterns = [
    url(r'^$', nansencloud.proc.views.ProcIndexView.as_view(), name='proc_index'),
    url(r'^products/$', nansencloud.proc.views.ProductsIndexView.as_view(), name='product_index'),
    url(r'^(?P<image_id>\d+)/$', nansencloud.cat.views.image, name='image'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/$', nansencloud.proc.views.proc_image, name='proc_image'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/(?P<bandName>\d+)/$',
        nansencloud.cat.views.band, name='band'),
    url(r'^(?P<chain_id>\d+)/(?P<image_id>\d+)/matchup/$', nansencloud.proc.views.matchup, name='band'),

]

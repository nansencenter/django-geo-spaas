from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'nansencloud.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    #url(r'^$', include('nansencloud.cat.urls')),
    #url(r'^cat/', include('nansencloud.cat.urls')),
    #url(r'^proc/', include('nansencloud.proc.urls')),
    url(r'^simple/', include('nansencloud.simple_viewer.urls')),
    url(r'^view/', include('nansencloud.viewer.urls')),
)

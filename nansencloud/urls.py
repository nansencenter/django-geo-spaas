from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'nansencloud.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$',      include('cat.urls')),
    url(r'^cat/',   include('cat.urls')),
    url(r'^proc/', include('proc.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

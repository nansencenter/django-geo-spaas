from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'djangosat.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$',      include('nansatcat.urls')),
    url(r'^cat/',   include('nansatcat.urls')),
    url(r'^proc/', include('nansatproc.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

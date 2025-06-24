from django.urls import include, path

from geospaas.config import config
from .views import GeoSPaaSView


app_name = 'base_viewer'

geospaas_apps = config.get_setting('base_viewer', 'apps')
urlpatterns = [
    path(
        route='',
        view=GeoSPaaSView.as_view(),
        name='index',
        kwargs={
            'geospaas_apps': geospaas_apps,
            'selected_tab': None,
        },
    )
]

for geospaas_app in geospaas_apps:
    urlpatterns.append(
        path(
            geospaas_app['path'],
            include(geospaas_app['urls']),
            {
                'geospaas_apps': geospaas_apps,
                'selected_tab': geospaas_app['label'],
            }
        )
    )

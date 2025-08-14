import importlib
import logging

from django.urls import include, path

from geospaas.config import config
from .views import GeoSPaaSView


logger = logging.getLogger(__name__)

app_name = 'base_viewer'
geospaas_apps = config['web_ui']['apps']


ui_patterns = [path('', view=GeoSPaaSView.as_view(), name='index')]
api_patterns = []
for geospaas_app in geospaas_apps:
    for patterns, module in ((ui_patterns, 'web_ui'), (api_patterns, 'web_api')):
        try:
            patterns.append(path(
                f"{geospaas_app['path']}/",
                include((
                    importlib.import_module(f"{geospaas_app['package']}.{module}"),
                    geospaas_app['path']))))
        except ModuleNotFoundError:
            logger.warning("%s.%s module not found", geospaas_app['package'], module)

urlpatterns = [
    path('', include(ui_patterns)),
    path('api/', include((api_patterns, 'api')))
]

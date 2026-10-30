import importlib
import logging

from django.urls import include, path

from geospaas.config import plugins_manager
from .views import GeoSPaaSView


logger = logging.getLogger(__name__)

app_name = 'geospaas'
urlpatterns = [
    path('', view=GeoSPaaSView.as_view(), name='index'),
]
for urls_module in plugins_manager.get_plugins_submodule('urls'):
    app_name = urls_module.app_name
    urlpatterns.append(path(f'{app_name}/', include(urls_module, app_name)))

import importlib
import logging

from django.urls import include, path

# import geospaas.catalog.urls
# import geospaas.vocabularies.urls
# import geospaas_harvesting.urls
from geospaas.config import web_plugins
from .views import GeoSPaaSView


logger = logging.getLogger(__name__)

app_name = 'geospaas'

urlpatterns = [
    path('', view=GeoSPaaSView.as_view(), name='index'),
]
for module_name in web_plugins:
    module = importlib.import_module(module_name)
    app_name = module.app_name
    urlpatterns.append(path(f'{app_name}/', include(module_name, app_name)))

import importlib
import logging

from django.urls import include, path

# import geospaas.catalog.urls
# import geospaas.vocabularies.urls
# import geospaas_harvesting.urls
from geospaas.config import get_plugins_urls
from .views import GeoSPaaSView


logger = logging.getLogger(__name__)

app_name = 'geospaas'
urlpatterns = [
    path('', view=GeoSPaaSView.as_view(), name='index'),
]
for urls_module in get_plugins_urls():
    app_name = urls_module.app_name
    urlpatterns.append(path(f'{app_name}/', include(urls_module, app_name)))

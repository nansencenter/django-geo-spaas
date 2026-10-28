import importlib
import logging
import types
import typing

import django.conf
from django.apps import apps


logger = logging.getLogger(__name__)


class PluginsManager():
    """Manage GeoSPaaS plugins"""

    def __init__(self):
        self.plugins = self._get_plugins(exclude=['geospaas', 'geospaas.base_viewer'])

    def _get_plugins(self, exclude:typing.Iterable[str]=None) -> set[str]:
        exclude = [] if exclude is None else exclude
        plugins = set()
        for app_config in apps.app_configs.values():
            if app_config.name.startswith('geospaas') and app_config.name not in exclude:
                plugins.add(app_config.name)
        return plugins

    def get_plugins_submodule(self, name: str) -> set[types.ModuleType]:
        submodules = set()
        for module_name in self.plugins:
            try:
                submodule = importlib.import_module(f"{module_name}.{name}")
                submodules.add(submodule)
            except ModuleNotFoundError:
                logger.debug("%s.%s not found", module_name, name)
        return submodules


plugins_manager = PluginsManager()


if __name__ == '__main__':
    pass

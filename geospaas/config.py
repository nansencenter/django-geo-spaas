import importlib
import logging
import types
import typing

import django.conf
from django.apps import apps


logger = logging.getLogger(__name__)


class Settings():
    """Class used to manage app settings"""
    def __init__(self, defaults: dict = None):
        self.defaults = defaults or {}

    def __getattr__(self, name):
        """Try getting the setting from the Django settings. If not
        available, use the default
        """
        return getattr(django.conf.settings, name, self.defaults.get(name, None))


class PluginsManager():
    """Manage GeoSPaaS plugins"""

    def __init__(self):
        self.plugins = self._get_plugins()

    def _get_plugins(self) -> set[str]:
        plugins = set()
        for app_config in apps.app_configs.values():
            if app_config.name.startswith('geospaas'):
                plugins.add(app_config.name)
        return plugins

    def get_plugins_submodule(self, name: str,
                              exclude: typing.Iterable[str] = set()) -> set[types.ModuleType]:
        submodules = set()
        for module_name in self.plugins:
            full_module_name = f"{module_name}.{name}"
            if full_module_name not in exclude:
                try:
                    submodule = importlib.import_module(full_module_name)
                    submodules.add(submodule)
                except ModuleNotFoundError:
                    logger.debug("%s.%s not found", module_name, name)
        return submodules


plugins_manager = PluginsManager()
settings = Settings({
    'GEOSPAAS_PYTHESINT_VERSIONS': None,
})


if __name__ == '__main__':
    pass

import importlib
import logging
import types
import typing

from django.apps import apps


logger = logging.getLogger(__name__)


def get_plugins(exclude:typing.Iterable[str]=None) -> set[str]:
    exclude = [] if exclude is None else exclude
    plugins = set()
    for app_config in apps.app_configs.values():
        if app_config.name.startswith('geospaas') and app_config.name not in exclude:
            plugins.add(app_config.name)
    return plugins


def get_plugins_urls() -> set[types.ModuleType]:
    urls_modules = set()
    for module_name in plugins:
        try:
            urls_module = importlib.import_module(f"{module_name}.urls")
            urls_modules.add(urls_module)
        except ModuleNotFoundError:
            logger.debug("%s.urls not found", module_name)
    return urls_modules


plugins = get_plugins(exclude=['geospaas', 'geospaas.base_viewer'])


if __name__ == '__main__':
    pass

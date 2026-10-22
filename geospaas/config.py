import importlib
import logging
import os
import types
import typing

import django
import django.conf
# Load Django settings to be able to interact with the database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geospaas_web.settings')
if not django.conf.settings.configured:
    django.setup()  # pragma: no cover

from django.apps import apps


logger = logging.getLogger(__name__)


def get_plugins(exclude:typing.Iterable[str]=None) -> set[str]:
    exclude = [] if exclude is None else exclude
    plugins = set()
    for app_config in apps.app_configs.values():
        if app_config.name.startswith('geospaas') and app_config.name not in exclude:
            plugins.add(app_config.name)
    return plugins


plugins = get_plugins(exclude=['geospaas', 'geospaas.base_viewer'])


def get_plugins_urls() -> set[types.ModuleType]:
    urls_modules = set()
    for module_name in plugins:
        try:
            urls_module = importlib.import_module(f"{module_name}.urls")
            urls_modules.add(urls_module)
        except ModuleNotFoundError:
            logger.debug("%s.urls not found", module_name)
    return urls_modules


def get_plugins_cli() -> set[types.ModuleType]:
    cli_modules = set()
    for module_name in plugins:
        try:
            cli_module = importlib.import_module(f"{module_name}.cli")
            cli_modules.add(cli_module)
        except ModuleNotFoundError:
            logger.debug("%s.cli not found", module_name)
    return cli_modules




if __name__ == '__main__':
    pass

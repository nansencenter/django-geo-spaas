import importlib
import itertools
import logging
import pkgutil
from pathlib import Path

import geospaas

logger = logging.getLogger(__name__)


def get_plugins(exclude=None):
    exclude = [] if exclude is None else exclude
    potential_plugins = itertools.chain(
        pkgutil.iter_modules(geospaas.__path__, prefix='geospaas.'),
        pkgutil.iter_modules())
    web_plugins = []
    cli_plugins = []
    for _, name, ispkg in potential_plugins:
        if ispkg and name.startswith('geospaas') and name not in exclude:
            package = importlib.import_module(name)
            module_files = [p.name for p in Path(package.__path__[0]).iterdir()]
            if "web_plugin.py" in module_files:
                web_plugins.append(f"{name}.web_plugin")
            if "cli_plugin.py" in module_files:
                cli_plugins.append(f"{name}.cli_plugin")
    return web_plugins, cli_plugins

web_plugins, cli_plugins = get_plugins(exclude=['geospaas.base_viewer'])


if __name__ == '__main__':
    pass

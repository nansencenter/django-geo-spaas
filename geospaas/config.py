import importlib
import logging
import pkgutil


logger = logging.getLogger(__name__)


class Config(dict):
    """"""


plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules()
    if name.startswith('geospaas_')
}


# placeholder for config file
config = Config({
    'web_ui': {
        'apps': [
            {'label': 'Catalog', 'path': 'catalog', 'package': 'geospaas.catalog'},
            {'label': 'Vocabularies', 'path': 'vocabularies', 'package': 'geospaas.vocabularies'},
            {'label': 'Harvesting', 'path': 'harvesting', 'package': 'geospaas_harvesting'},
        ]
    },
})

if __name__ == '__main__':
    pass

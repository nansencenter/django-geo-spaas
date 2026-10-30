import importlib
import pkgutil
from pathlib import Path

from geospaas.config import plugins_manager
from .base import Crawler
from ..utils import get_all_subclasses

# import crawlers modules from geospaas plugins
plugins = plugins_manager.get_plugins_submodule('crawlers')

# import crawlers modules from geospaas.harvesting
for (_, name, _) in pkgutil.iter_modules([Path(__file__).parent]):
    importlib.import_module('.' + name, __package__)

# create index that allows to retrieve a crawler class using its name
index = {
    cls.name: cls
    for cls in get_all_subclasses(Crawler)
    if cls.name is not None
}

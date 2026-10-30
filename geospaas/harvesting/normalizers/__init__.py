"""This package contains normalizers which extract the metadata
necessary to instantiate GeoSPaaS Datasets.
All normalizers in this package should inherit from
MetadataNormalizer.
"""
import pkgutil
import importlib
from pathlib import Path

from geospaas.config import plugins_manager
from .base import MetadataNormalizer, StreamMetadataNormalizer
from ..utils import get_all_subclasses

# import normalizers modules from geospaas plugins
plugins = plugins_manager.get_plugins_submodule('normalizers')

# import normalizers modules from geospaas.harvesting
for (_, name, _) in pkgutil.iter_modules([str(Path(__file__).parent)]):
    importlib.import_module('.' + name, __package__)

# create index that allows to retrieve a normalizer class using its name
index = {
    cls.name: cls
    for cls in get_all_subclasses(MetadataNormalizer)
    if cls.name is not None
}

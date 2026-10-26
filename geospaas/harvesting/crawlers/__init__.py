import importlib
import pkgutil
from pathlib import Path

from .base import Crawler
from ..utils import get_all_subclasses


for (_, name, _) in pkgutil.iter_modules([str(Path(__file__).parent)]):
        importlib.import_module('.' + name, __package__)

# index that allows to retrieve a normalizer class using its name
index = {
    cls.name: cls
    for cls in get_all_subclasses(Crawler)
    if cls.name is not None
}

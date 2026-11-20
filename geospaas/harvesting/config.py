"""Configuration management"""
import logging
from pathlib import Path

from geospaas.config import Settings
from .utils import read_yaml_file


logger = logging.getLogger(__name__)


settings = Settings({
    'GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES': True,
    'GEOSPAAS_HARVESTING_UPDATE_PYTHESINT': True,
    'GEOSPAAS_HARVESTING_PROVIDERS_PATH': Path(__file__).parent / 'default_providers.yml',
    'GEOSPAAS_HARVESTING_FAILED_INGESTIONS_PATH': Path('/', 'var', 'run', 'geospaas'),
})


class Configuration():
    """Base class for configuration objects"""

    def _parse_config(self, config_dict):
        """Parse a config dictionary and set the keys as properties of
        the current Configuration object
        """
        for name, value in self.config_arguments_parser.parse(config_dict).items():
            setattr(self, name, value)

    @classmethod
    def from_dict(cls, config_dict):
        """Creates a configuration object from a dictionary"""
        config = cls()
        config._parse_config(config_dict)
        return config

    @classmethod
    def from_file(cls, config_path):
        """Creates a configuration object from a YAML file"""
        return cls.from_dict(read_yaml_file(config_path))

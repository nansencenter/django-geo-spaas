"""Configuration management"""
import logging
from pathlib import Path

import geospaas.harvesting.utils as utils
import geospaas.harvesting.arguments as arguments
from .providers import Provider
from .utils import read_yaml_file


logger = logging.getLogger(__name__)


class NoProviderFoundError(Exception):
    """No provider class was found"""


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


class ProvidersArgument(arguments.DictArgument):
    """This argument is a dict of providers in the format:
    {
        'provider_name1':
            'crawler':
                'name': 'crawler1'
                'param1': 'value1'
        'provider_name2:
            'crawler':
                'name': 'crawler2'
                'param2': 'value2'
            'normalizer':
                'name': 'normalizer2'
            'ingester':
                'update': True
    }
    """

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def parse(self, value):
        """Go through the list of provider settings and create the
        providers
        """
        _providers = []
        providers_dict = super().parse(value)
        for provider_name, provider_config in providers_dict.items():
            _providers.append(Provider.from_config(provider_name, provider_config))
        return _providers


class GeneralConfiguration(Configuration):
    """Configuration manager for general harvesting settings"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_arguments_parser = arguments.ArgumentParser([
            arguments.BooleanArgument('update_vocabularies', default=True),
            arguments.BooleanArgument('update_pythesint', default=True),
            arguments.DictArgument('pythesint_versions', default=None),
            arguments.PathArgument('providers_path',
                                   default=Path(__file__).parent / 'default_providers.yml',
                                   description=('Path to the file containing the default '
                                                'providers definitions.'))
        ])


class ProvidersConfiguration(Configuration):
    """Configuration manager for providers"""
    def __init__(self):
        self.config_arguments_parser = arguments.ArgumentParser([
            ProvidersArgument('providers', required=True)
        ])


class SearchConfiguration(Configuration):
    """Configuration manager used to parse search parameters"""
    def __init__(self):
        self.config_arguments_parser = arguments.ArgumentParser([
            arguments.DictArgument('common', default=dict),
            arguments.ListArgument('searches', default=list)
        ])

    def create_provider_searches(self):
        """Creates a SearchResults object for each of the provider
        specific searches
        """
        searches = []
        for search in self.searches:  # pylint: disable=no-member
            provider_name = search.pop('provider_name')
            search_params = utils.merge_configs(self.common, search)
            searches.append(Provider.objects.get(name=provider_name).search(**search_params))
        return searches

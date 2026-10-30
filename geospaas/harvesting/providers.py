"""Base classes for use by providers"""
import logging

import django.db.models as models

import geospaas.harvesting.arguments as arguments
import geospaas.harvesting.config as config
import geospaas.harvesting.crawlers as crawlers
import geospaas.harvesting.ingesters as ingesters
import geospaas.harvesting.normalizers as normalizers
import geospaas.harvesting.utils as utils


logger = logging.getLogger(__name__)


class Provider(models.Model):
    """Offers an interface to search data from a type of provider or a
    specific provider. Uses crawlers, normalizers and ingesters to
    accomplish this.

    Allows saving a combination of crawler, normalizer and ingester
    configurations and manages instantiating the objects from that
    configuration. Providers can then be used when running searches.
    """
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    config = models.JSONField(null=False)

    class Meta:
        app_label = 'geospaas_harvesting'

    config_parser = arguments.ArgumentParser([
        arguments.DictArgument('crawler', required=True),
        arguments.DictArgument('normalizer', default={'name': 'raw'}),
        arguments.DictArgument('ingester', default=dict),
    ])

    @classmethod
    def from_config(cls, name, config):
        """Instantiate a provider from a config dictionary"""
        parsed_config = cls.config_parser.parse(config)

        # check that the crawler configuration is valid
        crawler_config = parsed_config['crawler'].copy()
        crawler_name = crawler_config.pop('name')
        crawlers.index[crawler_name].argument_parser.parse(crawler_config, allow_missing=True)

        return cls(name=name, config=parsed_config)

    def __repr__(self):
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"config={self.get_config_repr()})")

    def get_config_repr(self):
        """Returns a representation of the provider's configuration
        with masked passwords
        """
        config = self.config.copy()
        config['crawler'] = utils.mask_secrets(config['crawler'])
        return repr(config)

    def __str__(self):
        return (f"Provider: {self.name} ("
                f"normalizer: {self.normalizer_name}, "
                f"crawler: {self.crawler_name}"
                ")")

    def __eq__(self, other):
        return (
            type(self) is type(other) and
            self.name == other.name and
            self.config == other.config)

    @property
    def crawler_name(self):
        return self.config['crawler']['name']

    @property
    def normalizer_name(self):
        return self.config['normalizer']['name']

    def get_crawler_class(self, crawler_name):
        try:
            return crawlers.index[crawler_name]
        except KeyError:
            raise ValueError(f"Unknown crawler {crawler_name}")

    def get_normalizer_class(self, normalizer_name):
        try:
            return normalizers.index[normalizer_name]
        except KeyError:
            raise ValueError(f"Unknown normalizer {normalizer_name}")

    @staticmethod
    def get_config_section(config_dict, key):
        """Returns a config section without the 'name' attribute.
        Overrides values with `override_parameters` if provided
        """
        config_ = config_dict.get(key, {}).copy()
        name = config_.pop('name', None)
        return (name, config_)

    def search(self, **search_parameters):
        """Returns a Search object which can be used to explore the
        search results returned by the crawler
        """
        final_config = utils.merge_configs(self.config, search_parameters)
        crawler_name, crawler_config = self.get_config_section(final_config, 'crawler')
        normalizer_name, normalizer_config = self.get_config_section(final_config, 'normalizer')
        _, ingester_config = self.get_config_section(final_config, 'ingester')
        return SearchResults(
            crawler=self.get_crawler_class(crawler_name).from_config(crawler_config),
            normalizer=self.get_normalizer_class(normalizer_name)(**normalizer_config),
            ingester=ingesters.Ingester(**ingester_config))


class SearchResults():
    """Facilitates navigation in the results returned by a crawler and
    enables ingestion of the results in the database.
    Provides only basic functionality for now. To be extended when
    integrating the search and harvesting process in the web UI.
    """
    def __init__(self, crawler, normalizer, ingester):
        self.search_info = (
            f"crawler: {repr(crawler)}, "
            f"normalizer: {repr(normalizer)}, "
            f"ingester: {repr(ingester)}")
        self.results_iterable = normalizer.normalize_stream(crawler)
        self.ingester = ingester
        self._cached_results = []

    def __str__(self):
        return f"SearchResults for {self.search_info}"

    def __iter__(self):
        return iter(self.results_iterable)

    def save(self, **kwargs):
        """Save the datasets matching the search to the database"""
        logger.info("%s starting ingestion", self)
        self.ingester.ingest(self, **kwargs)

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


class ProvidersConfiguration(config.Configuration):
    """Configuration manager for providers"""
    def __init__(self):
        self.config_arguments_parser = arguments.ArgumentParser([
            ProvidersArgument('providers', required=True)
        ])


class SearchConfiguration(config.Configuration):
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

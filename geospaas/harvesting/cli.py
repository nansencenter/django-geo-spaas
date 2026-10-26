# pylint: disable=wrong-import-position
# pylint: disable=no-member
"""CLI for interacting with geospaas.harvesting"""
# TODO: manage URL checks and recovery
import argparse
import concurrent.futures
import logging
import os
import signal
from pathlib import Path
from typing import Union

import django
import django.conf
# Load Django settings to be able to interact with the database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geospaas.harvesting.settings')
if not django.conf.settings.configured:
    django.setup()  # pragma: no cover

import geospaas.harvesting.config as config
from geospaas.catalog.models import Parameter
from .providers import Provider
from .recovery import retry_ingest


logger = logging.getLogger(__name__)

package_dir = Path(__file__).parent
default_configuration_path = package_dir / 'config.yml'
# look in the folder from which the command is executed
default_search_path = Path() / 'search.yml'


class CreateDefaultProviders():
    """Flag used to signal that the default providers should be created
    """


def init_worker():
    """Initialization function for child processes. Defines signals handling."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def refresh_vocabularies(general_config):
    """Update the Vocabulary objects in the database if the
    `update_vocabularies` settings is True.
    If the `update_pythesint` setting is also True,
    the local pythesint data is also updated.
    """
    if general_config.update_vocabularies:
        logger.info('Updating vocabularies...')
        django.core.management.call_command(
            'update_vocabularies',
            force=general_config.update_pythesint,
            versions=general_config.pythesint_versions)
        logger.info('Finished updating vocabularies')
    # safety check in order to prevent harvesting process with an empty
    # list of parameters
    elif Parameter.objects.count() < 1:
        raise RuntimeError((
            "Parameters must be updated (with the 'update_vocabularies' command "
            "of django-geospaas) before the harvesting process"
        ))


def save_results(searches_results):
    """Ingests the results of each search in a separate process"""
    with concurrent.futures.ProcessPoolExecutor(initializer=init_worker) as executor:
        try:
            futures = []
            for search_results in searches_results:
                futures.append(executor.submit(search_results.save))

            for future in concurrent.futures.as_completed(futures):
                exception = future.exception()
                if exception:
                    logger.error(
                        "An exception happened during harvesting process",
                        exc_info=exception)
        except KeyboardInterrupt:
            executor.shutdown(wait=False)
            raise


def print_providers():
    """Print all existing providers"""
    print('Available providers:')
    for provider in Provider.objects.all():
        print(provider)


def delete_providers(names_to_delete: list[str]):
    """Delete the providers whose names are in `names_to_delete`"""
    to_delete = Provider.objects.filter(name__in=names_to_delete)
    print(f'Deleting {list(to_delete)}')
    to_delete.all().delete()


def update_providers(providers_path: Union[Path, str]):
    """Update providers from a file"""
    providers = config.ProvidersConfiguration.from_file(providers_path).providers
    print(f"Updating providers from {providers_path}")
    for provider in providers:
        try:
            existing_provider = Provider.objects.get(name=provider.name)
        except Provider.DoesNotExist:
            print(f"Creating provider {provider}")
            provider.save()
        else:
            if provider.config != existing_provider.config:
                print(f"Updating provider {existing_provider} to {provider}")
                provider.id = existing_provider.id
                provider.save()


def handle_providers(cli_arguments):
    """List/update/delete providers"""
    general_config = config.GeneralConfiguration.from_file(cli_arguments.config_path)
    if cli_arguments.providers_path:
        if cli_arguments.providers_path is CreateDefaultProviders:
            providers_path = general_config.providers_path
        else:
            providers_path = cli_arguments.providers_path
        update_providers(providers_path)
    elif cli_arguments.delete:
        delete_providers(cli_arguments.delete)
    elif cli_arguments.list:
        print_providers()


def harvest(cli_arguments):
    """Reads the configuration files and harvests the searched data.
    If errors occur during the ingestion process (like the provider
    website being temporarily unavailable), it is retried at the end.
    """
    general_config = config.GeneralConfiguration.from_file(cli_arguments.config_path)
    search_config = config.SearchConfiguration.from_file(cli_arguments.search_path)
    searches_results = search_config.create_provider_searches()

    refresh_vocabularies(general_config)
    save_results(searches_results)

    # Retry to ingest datasets for which the ingestion failed
    retry_ingest()


def make_arg_parser():
    """Creates a parser for the CLI arguments"""
    arg_parser = argparse.ArgumentParser(
        prog='harvesting',
        description='CLI for searching and harvesting data for the GeoSPaaS catalog')
    arg_parser.add_argument('-c', '--config',
                            dest='config_path',
                            default=default_configuration_path,
                            help='Path to the configuration file')

    subparsers = arg_parser.add_subparsers()

    providers_subparser = subparsers.add_parser('providers', help='Provider functions')
    providers_subparser.set_defaults(func=handle_providers)
    action_group = providers_subparser.add_mutually_exclusive_group()
    action_group.add_argument('-u', '--update',
                              dest='providers_path',
                              default=None,
                              const=CreateDefaultProviders,
                              nargs="?",
                              help='Create/update providers from YAML file. '
                                   'If no file is provided, use the default file')
    action_group.add_argument('-d', '--delete', action='extend', nargs='+', type=str,
                              help='Delete providers')
    action_group.add_argument('-l', '--list', action='store_true', help='List providers')

    harvest_parser = subparsers.add_parser('harvest',
                                           help='Harvest data directly into the database')
    harvest_parser.add_argument('-s', '--search',
                                dest='search_path',
                                default=default_search_path,
                                help='Path to the file containing the search parameters')
    harvest_parser.set_defaults(func=harvest)
    return arg_parser


def main():
    """Parse the CLI arguments and call the function corresponding to
    the invoked subcommand
    """
    arg_parser = make_arg_parser()
    cli_arguments = arg_parser.parse_args()
    cli_arguments.func(cli_arguments)


if __name__ == '__main__':  # pragma: no cover
    main()

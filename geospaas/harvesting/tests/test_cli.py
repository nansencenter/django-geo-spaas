"""Tests for the CLI"""
import argparse
import contextlib
import io
import logging
import unittest.mock as mock
import signal

import django.test

import geospaas.harvesting.cli as cli
from geospaas.harvesting.models import Provider


class CLITestCase(django.test.TestCase):
    """Tests for the CLI"""

    fixtures = ['harvesting_providers']

    def test_init_worker(self):
        """Workers must ignore SIGINT"""
        cli.init_worker()
        self.assertEqual(signal.getsignal(signal.SIGINT), signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def test_refresh_vocabularies(self):
        """The database vocabulary objects must be updated
        only if the corresponding setting is True
        """
        with mock.patch('django.core.management.call_command') as mock_call_command, \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings, \
             mock.patch('geospaas.config.settings') as mock_geospaas_settings:
            mock_settings.GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES = True
            mock_settings.GEOSPAAS_HARVESTING_UPDATE_PYTHESINT = False
            mock_geospaas_settings.GEOSPAAS_PYTHESINT_VERSIONS = None
            with self.assertLogs(logger=cli.logger, level=logging.INFO):
                cli.refresh_vocabularies()
            mock_call_command.assert_called_with('update_vocabularies', force=False, versions=None)

    def test_no_refresh_vocabularies(self):
        """The vocabularies should not be refreshed if the setting is
        False
        """
        with mock.patch('django.core.management.call_command') as mock_call_command, \
             mock.patch('geospaas.vocabularies.models.Parameter.objects.count', return_value=2), \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES = False
            cli.refresh_vocabularies()
            mock_call_command.assert_not_called()

    def test_refresh_vocabularies_parameters_error(self):
        """Test that an exception is raised if no refresh is requested
        and there are no Parameters in the database
        """
        with mock.patch('geospaas.vocabularies.models.Parameter.objects.count', return_value=0), \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES = False
            with self.assertRaises(RuntimeError):
                cli.refresh_vocabularies()

    def test_refresh_vocabularies_and_update_pythesint(self):
        """The database vocabulary objects must be updated and
        pythesint's data refreshed only if the corresponding settings
        are both True
        """
        with mock.patch('geospaas.harvesting.config.settings') as mock_settings, \
             mock.patch('geospaas.config.settings') as mock_geospaas_settings:

            with mock.patch('django.core.management.call_command') as mock_call_command:
                # Refresh the database but not the pythesint files
                mock_settings.GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES = True
                mock_settings.GEOSPAAS_HARVESTING_UPDATE_PYTHESINT = False
                mock_geospaas_settings.GEOSPAAS_PYTHESINT_VERSIONS = None
                with self.assertLogs(logger=cli.logger, level=logging.INFO):
                    cli.refresh_vocabularies()
                mock_call_command.assert_called_with('update_vocabularies', force=False, versions=None)

            with mock.patch('django.core.management.call_command') as mock_call_command:
                # Refresh both the database and the pythesint files
                mock_settings.GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES = True
                mock_settings.GEOSPAAS_HARVESTING_UPDATE_PYTHESINT = True
                mock_geospaas_settings.GEOSPAAS_PYTHESINT_VERSIONS = None
                with self.assertLogs(logger=cli.logger, level=logging.INFO):
                    cli.refresh_vocabularies()
                mock_call_command.assert_called_with('update_vocabularies', force=True, versions=None)

            with mock.patch('django.core.management.call_command') as mock_call_command:
                # Refresh both the database and the pythesint files,
                # specifying versions
                mock_settings.GEOSPAAS_HARVESTING_UPDATE_VOCABULARIES = True
                mock_settings.GEOSPAAS_HARVESTING_UPDATE_PYTHESINT = True
                mock_geospaas_settings.GEOSPAAS_PYTHESINT_VERSIONS = {'gcmd_instrument': '9.1.5'}
                with self.assertLogs(logger=cli.logger, level=logging.INFO):
                    cli.refresh_vocabularies()
                mock_call_command.assert_called_with(
                    'update_vocabularies',
                    force=True,
                    versions={'gcmd_instrument': '9.1.5'})

    def test_save_results(self):
        """Test the the save() method of SearchResults objects is
        called in separate processes
        """
        searches_results = [mock.Mock(), mock.Mock()]
        error_future = mock.Mock()
        error_future.exception.return_value = RuntimeError
        futures = [mock.Mock(), error_future]

        with mock.patch('concurrent.futures.ProcessPoolExecutor.submit',
                        side_effect=futures) as mock_submit, \
             mock.patch('concurrent.futures.as_completed', side_effect=iter) as mock_as_completed, \
             self.assertLogs(cli.logger, level=logging.ERROR):
            cli.save_results(searches_results)

        mock_submit.assert_has_calls([
            mock.call(search_results.save) for search_results in searches_results
        ])
        mock_as_completed.assert_called_with(futures)

    def test_save_results_keyboard_interrupt(self):
        """Test KeyboardIbnterrupt handling"""
        with mock.patch('concurrent.futures.ProcessPoolExecutor') as mock_executor_builder:
            mock_executor = mock_executor_builder.return_value.__enter__.return_value
            mock_executor.submit.side_effect = KeyboardInterrupt
            with self.assertRaises(KeyboardInterrupt):
                cli.save_results([mock.Mock()])
        mock_executor.shutdown.assert_called()

    def test_print_providers(self):
        """Test printing providers help texts"""
        with contextlib.redirect_stdout(io.StringIO()) as out:
            cli.print_providers(),
            self.assertEqual(
                out.getvalue(),
                'Available providers:\n'
                'Provider: ftp (normalizer: raw, crawler: ftp)\n'
                'Provider: thredds (normalizer: raw, crawler: thredds)\n'
                'Provider: ceda (normalizer: ceda_esa_cci, crawler: ftp)\n')

    def test_delete_providers(self):
        """Test deleting providers"""
        with mock.patch('builtins.print') as mock_print:
            cli.delete_providers(['ceda', 'thredds'])
        providers = Provider.objects.all()
        self.assertEqual(providers.count(), 1)
        self.assertEqual(providers.first().name, 'ftp')

    def test_update_providers_create_new(self):
        """Test that new providers are created if they do not exist"""
        providers_path = '/path/to/providers.yml'
        new_provider = Provider.from_config('test', {
            "crawler": {"name": "html_directory"},
            "ingester": {},
            "normalizer": {"name": "raw"}
        })
        mock_config = mock.Mock()
        mock_config.providers = [new_provider]

        with mock.patch('geospaas.harvesting.cli.ProvidersConfiguration.from_file',
                        return_value=mock_config), \
                mock.patch('builtins.print') as mock_print:
            cli.update_providers(providers_path)

        mock_print.assert_any_call(f"Creating provider {new_provider}")
        self.assertEqual(Provider.objects.count(), 4)
        self.assertIn(new_provider, Provider.objects.all())

    def test_update_providers_update_existing(self):
        """Test that existing providers are updated if they differ"""
        providers_path = '/path/to/providers.yml'
        updated_provider = Provider.from_config('ftp', {
            "crawler": {"name": "ftp"},
            "ingester": {"update": True},
            "normalizer": {"name": "raw"}
        })
        mock_config = mock.Mock()
        mock_config.providers = [updated_provider]

        provider_before = Provider.objects.get(name='ftp')

        with mock.patch('geospaas.harvesting.cli.ProvidersConfiguration.from_file',
                        return_value=mock_config), \
                mock.patch('builtins.print') as mock_print:
            cli.update_providers(providers_path)

        provider_after = Provider.objects.get(name='ftp')
        updated_provider.refresh_from_db

        mock_print.assert_any_call(f"Updating provider {provider_before} to {updated_provider}")
        self.assertEqual(Provider.objects.count(), 3)
        self.assertEqual(provider_after, updated_provider)
        self.assertNotEqual(provider_before, provider_after)

    def test_update_providers_no_update_needed(self):
        """Test that no update occurs if the provider already matches"""
        providers_path = '/path/to/providers.yml'
        updated_provider = Provider.from_config('ftp', {
            "crawler": {"name": "ftp"},
            "ingester": {},
            "normalizer": {"name": "raw"}
        })
        mock_config = mock.Mock()
        mock_config.providers = [updated_provider]

        provider_before = Provider.objects.get(name='ftp')

        with mock.patch('geospaas.harvesting.cli.ProvidersConfiguration.from_file',
                        return_value=mock_config), \
                mock.patch('builtins.print') as mock_print:
            cli.update_providers(providers_path)

        provider_after = Provider.objects.get(name='ftp')

        mock_print.assert_has_calls((
            mock.call('Updating providers from /path/to/providers.yml'),))
        self.assertEqual(provider_before, provider_after)

    def test_harvest(self):
        """Check that the necessary functions are called"""
        with mock.patch('geospaas.harvesting.cli.SearchConfiguration'), \
             mock.patch('geospaas.harvesting.cli.refresh_vocabularies') as mock_refresh_vocs, \
             mock.patch('geospaas.harvesting.cli.save_results') as mock_save_results, \
             mock.patch('geospaas.harvesting.cli.retry_ingest') as mock_retry_ingest:
            cli.harvest(mock.Mock())

            mock_refresh_vocs.assert_called()
            mock_save_results.assert_called()
            mock_retry_ingest.assert_called()

    def test_make_arg_parser(self):
        """Test making the CLI arguments parser"""
        arg_parser = cli.make_arg_parser()
        parsed_args = arg_parser.parse_args((
            'harvest',
            '-s', '/foo/search.yml'))
        self.assertEqual(
            parsed_args,
            argparse.Namespace(
                search_path='/foo/search.yml',
                func=cli.harvest))

    def test_main(self):
        """Test the right function is called in accord with the CLI
        arguments
        """
        with mock.patch('sys.argv', ['test_cli.py', 'harvest']), \
             mock.patch('geospaas.harvesting.cli.harvest') as mock_harvest:
            cli.main()
            mock_harvest.assert_called()

    def test_handle_providers_update(self):
        """Test that providers are updated when --update is passed"""
        cli_arguments = argparse.Namespace(
            providers_path='/path/to/providers.yml', delete=None, list=False)

        with mock.patch('geospaas.harvesting.cli.update_providers') as mock_update_providers, \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_PROVIDERS_PATH ='/default.yml'
            cli.handle_providers(cli_arguments)

        mock_update_providers.assert_called_once_with('/path/to/providers.yml')

    def test_handle_providers_update_default(self):
        """Test that default providers are updated when --update is passed without a path"""
        cli_arguments = argparse.Namespace(
            providers_path=cli.CreateDefaultProviders, delete=None, list=False)

        with mock.patch('geospaas.harvesting.cli.update_providers') as mock_update_providers, \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_PROVIDERS_PATH ='/default.yml'
            cli.handle_providers(cli_arguments)

        mock_update_providers.assert_called_once_with('/default.yml')

    def test_handle_providers_delete(self):
        """Test that providers are deleted when --delete is passed"""
        cli_arguments = argparse.Namespace(
            providers_path=None, delete=['provider1', 'provider2'], list=False)

        with mock.patch('geospaas.harvesting.cli.delete_providers') as mock_delete_providers, \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_PROVIDERS_PATH ='/default.yml'
            cli.handle_providers(cli_arguments)

        mock_delete_providers.assert_called_once_with(['provider1', 'provider2'])

    def test_handle_providers_list(self):
        """Test that providers are listed when --list is passed"""
        cli_arguments = argparse.Namespace(providers_path=None, delete=None, list=True)

        with mock.patch('geospaas.harvesting.cli.print_providers') as mock_print_providers, \
             mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_PROVIDERS_PATH ='/default.yml'
            cli.handle_providers(cli_arguments)

        mock_print_providers.assert_called_once()

    def test_handle_providers_no_action(self):
        """Test that no action is taken when no arguments are passed"""
        cli_arguments = argparse.Namespace(providers_path=None, delete=None, list=False)

        with mock.patch('geospaas.harvesting.cli.update_providers') as mock_update_providers, \
                mock.patch('geospaas.harvesting.cli.delete_providers') as mock_delete_providers, \
                mock.patch('geospaas.harvesting.cli.print_providers') as mock_print_providers, \
                mock.patch('geospaas.harvesting.config.settings') as mock_settings:
            mock_settings.GEOSPAAS_HARVESTING_PROVIDERS_PATH ='/default.yml'
            cli.handle_providers(cli_arguments)

        mock_update_providers.assert_not_called()
        mock_delete_providers.assert_not_called()
        mock_print_providers.assert_not_called()

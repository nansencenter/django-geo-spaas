""" Test the verification code """
# pylint: disable=protected-access
import argparse
import io
import logging
import ftplib
import os
import os.path
import socket
import textwrap
import unittest
import unittest.mock as mock

import requests.auth
import requests.exceptions
import requests_oauthlib

import geospaas.harvesting.verify_urls as verify_urls


class ProviderTestCase(unittest.TestCase):
    """Test the Provider base class"""

    def test_instantiation(self):
        """Test the setting of the base properties"""
        name = 'test'
        config = {'foo': 'bar', 'baz': 'qux'}
        provider = verify_urls.Provider(name, config)
        self.assertEqual(provider.name, name)
        self.assertEqual(provider.config, config)
        self.assertIsNone(provider._auth)

    def test_equality(self):
        """Test the equlity operator between two Provider objects"""
        self.assertEqual(
            verify_urls.Provider('test', {'foo': 'bar'}),
            verify_urls.Provider('test', {'foo': 'bar'}))
        self.assertNotEqual(
            verify_urls.Provider('test', {'foo': 'bar'}),
            verify_urls.Provider('test2', {'foo': 'bar'}))
        self.assertNotEqual(
            verify_urls.Provider('test', {'foo': 'bar'}),
            verify_urls.Provider('test', {'baz': 'qux'}))

    def test_abstract_auth(self):
        """The auth property should raise a NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            verify_urls.Provider('test', {}).auth

    def test_abstract_check_url(self):
        """The check_url() method should raise a NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            verify_urls.Provider('test', {}).check_url(mock.Mock())

    def test_abstract_check_all_urls(self):
        """The check_all_urls() method should raise a NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            verify_urls.Provider('test', {}).check_all_urls('file')

    def test_write_stale_url(self):
        """Test writing URL checking information to a file"""
        with mock.patch('geospaas.harvesting.verify_urls.open') as mock_open:
            mock_file = mock.MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            with self.assertLogs(verify_urls.logger, level=logging.DEBUG):
                verify_urls.Provider('test', {}).write_stale_url(
                    'file_name',
                    'absent',
                    518,
                    'http://foo/bar.nc')
            mock_file.write.assert_called_once_with(f"absent 518 http://foo/bar.nc{os.linesep}")


class HTTPProviderTestCase(unittest.TestCase):
    """Test the HTTPProvider class"""

    def test_instantiation(self):
        """Test that the attributes are correctly initialized"""
        provider = verify_urls.HTTPProvider('test', {'foo': 'bar'})
        self.assertEqual(provider.name, 'test')
        self.assertEqual(provider.config, {'foo': 'bar'})
        self.assertEqual(provider._auth_start, None)

    def test_build_oauth2(self):
        """Should return an OAuth2 object usable by `requests`"""
        with mock.patch('requests_oauthlib.OAuth2Session') as mock_oauth2_session:
            self.assertIsInstance(
                verify_urls.HTTPProvider.build_oauth2('user', 'pass', 'https://foo', 'CLIENT'),
                requests_oauthlib.OAuth2)
            mock_oauth2_session.return_value.fetch_token.assert_called_with(
                token_url='https://foo',
                username='user',
                password='pass',
                client_id='CLIENT'
            )

    def test_auth_oauth2(self):
        """The auth property should return the right authentication
        object based on the provider attributes
        """
        provider = verify_urls.HTTPProvider('test', {
            'username': 'user',
            'password': 'pass',
            'token_url': 'https://foo',
            'client_id': 'CLIENT'
        })

        mock_oauth2 = mock.Mock()
        with mock.patch('geospaas.harvesting.verify_urls.HTTPProvider.build_oauth2',
                        return_value=mock_oauth2) as mock_build_oauth2:
            self.assertEqual(
                provider.auth,
                mock_oauth2)
            mock_build_oauth2.assert_called_once_with('user', 'pass', 'https://foo', 'CLIENT')

    def test_auth_basic(self):
        """The auth property should return the right authentication
        object based on the provider attributes
        """
        provider = verify_urls.HTTPProvider('test', {'username': 'user', 'password': 'pass'})
        self.assertEqual(
            provider.auth,
            requests.auth.HTTPBasicAuth('user', 'pass'))

    def test_auth_no_auth(self):
        """The auth property should return None when no authentication
        method can be determined
        """
        provider = verify_urls.HTTPProvider('test', {})
        self.assertIsNone(provider.auth)

    def test_auth_renew(self):
        """Test that authentication is renewed when necessary"""
        provider = verify_urls.HTTPProvider('test', {
            'username': 'user',
            'password': 'pass',
            'token_url': 'token',
            'client_id': 'ID',
            'auth_renew': 1
        })

        with mock.patch('time.monotonic', side_effect=(1, 2, 2.1)), \
             mock.patch('geospaas.harvesting.verify_urls.HTTPProvider.build_oauth2',
                        side_effect=('auth1', 'auth2', 'auth3')):
            # First call -> first return value from build_oauth2()
            self.assertEqual(provider.auth, 'auth1')
            # Second call, one second later -> second return value from build_oauth2()
            self.assertEqual(provider.auth, 'auth2')
            # Third call, less than one second later -> the value does not change
            self.assertEqual(provider.auth, 'auth2')

    def test_check_url_200(self):
        """Should send a HEAD request to the URL and return whether the
        URL is valid or not.
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        mock_response = mock.MagicMock(status_code=200, headers={})
        with mock.patch('geospaas.harvesting.utils.http_request', return_value=mock_response):
            self.assertEqual(provider.check_url(mock_dataset_uri), verify_urls.PRESENT)

    def test_check_url_404(self):
        """Should send a HEAD request to the URL and return
        verify_urls.ABSENT if a 404 error is received
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        mock_response = mock.MagicMock(status_code=404, headers={})
        with mock.patch('geospaas.harvesting.utils.http_request',
                        return_value=mock_response) as mock_request:
            self.assertEqual(provider.check_url(mock_dataset_uri), verify_urls.ABSENT)
            mock_request.assert_called_once()

    def test_check_url_http_error(self):
        """Should send a HEAD request to the URL and return
        'http_<error_code>' if an error code other than 404 is received
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        mock_response = mock.MagicMock(status_code=503, headers={})
        with mock.patch('geospaas.harvesting.utils.http_request',
                        return_value=mock_response) as mock_request:
            self.assertEqual(provider.check_url(mock_dataset_uri), 'http_503')
            mock_request.assert_called_once()

    def test_check_url_429_no_header(self):
        """When an error 429 occurs, the URL should ne retried after a
        delay
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        mock_responses = (
            mock.MagicMock(status_code=429, headers={}),
            mock.MagicMock(status_code=404, headers={})
        )
        with mock.patch('geospaas.harvesting.utils.http_request',
                        side_effect=mock_responses) as mock_request, \
                mock.patch('time.sleep') as mock_sleep:

            with self.assertLogs(verify_urls.logger, level=logging.WARNING):
                self.assertEqual(provider.check_url(mock_dataset_uri),verify_urls.ABSENT)

            self.assertEqual(mock_request.call_count, 2)
            self.assertListEqual(mock_sleep.call_args_list, [mock.call(60), mock.call(0)])

    def test_check_url_429_retry_after_header(self):
        """When an error 429 occurs, the URL should be retried after a
        delay
        """
        provider = verify_urls.HTTPProvider('test', {'throttle': 1})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        mock_responses = (
            mock.MagicMock(status_code=429, headers={'Retry-After': 2}),
            mock.MagicMock(status_code=200, headers={})
        )
        with mock.patch('geospaas.harvesting.utils.http_request',
                        side_effect=mock_responses) as mock_request, \
                mock.patch('time.sleep') as mock_sleep:

            with self.assertLogs(verify_urls.logger, level=logging.WARNING):
                self.assertEqual(
                    provider.check_url(mock_dataset_uri),
                    verify_urls.PRESENT)

            self.assertEqual(mock_request.call_count, 2)
            self.assertListEqual(mock_sleep.call_args_list, [mock.call(2), mock.call(1)])

    def test_check_url_429_too_many_retries(self):
        """When there are too many retries, an exception should be
        raised
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        mock_responses = (
            mock.MagicMock(status_code=429, headers={}),
            mock.MagicMock(status_code=200, headers={})
        )
        with mock.patch('geospaas.harvesting.utils.http_request',
                        side_effect=mock_responses) as mock_request:

            with self.assertRaises(verify_urls.TooManyRequests):
                provider.check_url(mock_dataset_uri, tries=1)
            mock_request.assert_called_once()

    def test_check_url_connection_error_retry(self):
        """The request should be retried if a ConnectionError occurs"""
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        with mock.patch('geospaas.harvesting.utils.http_request') as mock_request, \
             mock.patch('time.sleep') as mock_sleep:
            mock_request.side_effect = (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectionError,
                mock.MagicMock(status_code=200, headers={})
            )
            with self.assertLogs(verify_urls.logger, level=logging.ERROR):
                provider.check_url(mock_dataset_uri, tries=5)

        self.assertListEqual(mock_sleep.call_args_list, [mock.call(5), mock.call(5), mock.call(0)])

    def test_check_url_connection_error_too_many_retries(self):
        """The request should be retried if a ConnectionError occurs
        and the exception should be raised if the retry limit is
        reached
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_dataset_uri = mock.Mock(id=1, uri='https://foo')
        with mock.patch('geospaas.harvesting.utils.http_request') as mock_request, \
                mock.patch('time.sleep') as mock_sleep:
            mock_request.side_effect = (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectionError,
            )
            with self.assertLogs(verify_urls.logger, level=logging.ERROR), \
                 self.assertRaises(requests.exceptions.ConnectionError):
                provider.check_url(mock_dataset_uri, tries=2)

        self.assertListEqual(mock_sleep.call_args_list, [mock.call(5)])

    def test_check_and_write_stale_url_valid(self):
        """Should not write anything to the output file if the URL is
        valid
        """
        provider = verify_urls.HTTPProvider('test', {})
        mock_lock = mock.MagicMock()
        with mock.patch('geospaas.harvesting.verify_urls.HTTPProvider.check_url',
                        return_value=verify_urls.PRESENT), \
                mock.patch('geospaas.harvesting.verify_urls.open') as mock_open:
            provider.check_and_write_stale_url(mock_lock, 'output.txt', mock.Mock())
            mock_open.assert_not_called()

    def test_check_and_write_stale_url_invalid(self):
        """Should write the URL info to the output file if the URL is
        invalid
        """
        provider = verify_urls.HTTPProvider('test', {})
        with mock.patch('geospaas.harvesting.verify_urls.HTTPProvider.check_url',
                        return_value=verify_urls.ABSENT), \
                mock.patch('geospaas.harvesting.verify_urls.open') as mock_open:
            mock_file = mock.MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_dataset_uri = mock.Mock()
            mock_dataset_uri.id = 1
            mock_dataset_uri.uri = 'https://foo'
            provider.check_and_write_stale_url(mock.MagicMock(), 'output.txt', mock_dataset_uri)
            mock_file.write.assert_called_once_with(
                f"{verify_urls.ABSENT} 1 https://foo{os.linesep}")

    def test_check_all_urls(self):
        """Should check all the URLs for one provider"""
        mock_lock = mock.Mock()
        with mock.patch('geospaas.harvesting.verify_urls.Lock', return_value=mock_lock), \
                mock.patch(
                    'geospaas.harvesting.verify_urls.BoundedThreadPoolExecutor') as mock_pool, \
                mock.patch('geospaas.harvesting.verify_urls.DatasetURI.objects') as mock_manager, \
                mock.patch('concurrent.futures.as_completed'), \
                mock.patch('geospaas.harvesting.verify_urls.HTTPProvider'
                           '.check_and_write_stale_url') as mock_write:
            mock_executor = mock_pool.return_value.__enter__.return_value
            mock_dataset_uri = mock.Mock()
            mock_manager.filter.return_value.iterator.return_value = [mock_dataset_uri]

            # call without throttle: 50 workers
            provider = verify_urls.HTTPProvider('test', {'url': 'https://foo/'})
            with self.assertLogs(verify_urls.logger, level=logging.INFO):
                provider.check_all_urls('output.txt')

            mock_executor.submit.assert_called_once_with(
                mock_write, mock_lock, 'output.txt', mock_dataset_uri)
            mock_pool.assert_called_once_with(max_workers=50, queue_limit=2000)

            mock_pool.reset_mock()

            # call with throttle: 1 worker
            provider = verify_urls.HTTPProvider('test', {'url': 'https://foo/', 'throttle': 1})
            with self.assertLogs(verify_urls.logger, level=logging.INFO):
                provider.check_all_urls('output.txt')
            mock_executor.submit.assert_called_once_with(
                mock_write, mock_lock, 'output.txt', mock_dataset_uri)
            mock_pool.assert_called_once_with(max_workers=1, queue_limit=2000)

            mock_pool.reset_mock()

    def test_check_all_urls_thread_error(self):
        """Exceptions happening in the threads should be raised in the
        main thread
        """
        provider = verify_urls.HTTPProvider('test', {'url': 'https://foo'})
        with mock.patch('geospaas.harvesting.verify_urls.HTTPProvider'
                        '.check_and_write_stale_url') as mock_write, \
                mock.patch('geospaas.harvesting.verify_urls.DatasetURI.objects') as mock_manager:
            mock_write.side_effect = ValueError
            mock_manager.filter.return_value.iterator.return_value = [mock.Mock()]
            with self.assertRaises(ValueError), \
                    self.assertLogs(verify_urls.logger, level=logging.INFO):
                provider.check_all_urls('out.txt')


class FTPProviderTestCase(unittest.TestCase):
    """Test the FTPProvider class"""

    def test_instantiation(self):
        """Test that the attributes are correctly initialized"""
        provider = verify_urls.FTPProvider('test', {'foo': 'bar'})
        self.assertEqual(provider.name, 'test')
        self.assertEqual(provider.config, {'foo': 'bar'})
        self.assertEqual(provider._ftp_client, None)

    def test_auth(self):
        """Test that the auth property returns a dictionary of
        arguments for ftplib.FTP.login() if the necessary information
        is provided
        """
        # No authentication
        provider = verify_urls.FTPProvider('test', {})
        self.assertEqual(provider.auth, {'user': '', 'passwd': ''})

        # Authentication info provided
        provider = verify_urls.FTPProvider('test', {'username': 'user', 'password': 'pass'})
        provider_auth = provider.auth
        self.assertEqual(provider_auth, {'user': 'user', 'passwd': 'pass'})

        # Return existing auth
        self.assertIs(provider.auth, provider_auth)

    def test_ftp_client(self):
        """Test that an FTP client is provided by the ftp_client property"""
        provider = verify_urls.FTPProvider('test', {})
        with mock.patch.object(provider, 'ftp_connect') as mock_ftp_connect:
            ftp_client = provider.ftp_client
            self.assertIsInstance(provider.ftp_client, ftplib.FTP)
            mock_ftp_connect.assert_called_once()

            mock_ftp_connect.reset_mock()

            # Check that the client is re-used on following calls
            self.assertIs(provider.ftp_client, ftp_client)
            mock_ftp_connect.assert_not_called()

    def test_ftp_connect(self):
        """Test FTP connection in a standard case"""
        provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client:
            provider.ftp_connect()
            mock_ftp_client.return_value.connect.assert_called_with('foo', timeout=5)
            mock_ftp_client.return_value.login.assert_called_with(user='', passwd='')

    def test_ftp_connect_with_auth(self):
        """Test FTP connection with authentication"""
        provider = verify_urls.FTPProvider('test', {
            'url': 'ftp://foo',
            'username': 'user',
            'password': 'pass'
        })
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client:
            provider.ftp_connect()
            mock_ftp_client.return_value.connect.assert_called_with('foo', timeout=5)
            mock_ftp_client.return_value.login.assert_called_with(user='user', passwd='pass')

    def test_ftp_connect_ok_after_retry(self):
        """Test FTP connection with retries, successful in the end"""
        provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client, \
             mock.patch('time.sleep') as mock_sleep:
            mock_ftp_client.return_value.connect.side_effect = (socket.timeout(),) * 3 + ('220',)

            provider.ftp_connect()

            mock_ftp_client.return_value.connect.assert_called_with('foo', timeout=5)
            self.assertEqual(mock_ftp_client.return_value.connect.call_count, 4)

            mock_ftp_client.return_value.login.assert_called_once_with(user='', passwd='')

            self.assertListEqual(
                mock_sleep.call_args_list,
                [mock.call(5), mock.call(6), mock.call(7)])

    def test_ftp_connect_failing_after_retry(self):
        """Test FTP connection with retries, failing in the end"""
        provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client, \
                mock.patch('time.sleep') as mock_sleep:
            mock_ftp_client.return_value.connect.side_effect = socket.timeout

            with self.assertRaises(socket.timeout), \
                 self.assertLogs(verify_urls.logger, level=logging.ERROR):
                provider.ftp_connect()

            self.assertEqual(mock_ftp_client.return_value.connect.call_count, 5)
            mock_ftp_client.return_value.login.assert_not_called()
            self.assertListEqual(
                mock_sleep.call_args_list,
                [mock.call(5), mock.call(6), mock.call(7), mock.call(8)])

    def test_check_url_present(self):
        """Test checking a URL that points to an existing file"""
        mock_dataset_uri = mock.Mock()
        mock_dataset_uri.uri = 'ftp://foo/bar/baz.nc'
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client:

            mock_ftp_client.return_value.nlst.return_value = ['/bar/baz.nc']
            provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})

            self.assertEqual(
                provider.check_url(mock_dataset_uri),
                verify_urls.PRESENT)

    def test_check_url_absent(self):
        """Test checking a URL that points to an non-existing file"""
        mock_dataset_uri = mock.Mock()
        mock_dataset_uri.uri = 'ftp://foo/bar/baz.nc'
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client:

            mock_ftp_client.return_value.nlst.return_value = []
            provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})

            self.assertEqual(
                provider.check_url(mock_dataset_uri),
                verify_urls.ABSENT)

    def test_check_url_ok_after_retries(self):
        """Test checking a URL successfully after some retries"""
        mock_dataset_uri = mock.Mock()
        mock_dataset_uri.uri = 'ftp://foo/bar/baz.nc'
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client, \
             mock.patch('time.sleep') as mock_sleep:

            mock_ftp_client.return_value.nlst.side_effect = (
                (ConnectionResetError,) * 3 + (verify_urls.ABSENT,))
            provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})

            self.assertEqual(
                provider.check_url(mock_dataset_uri),
                verify_urls.ABSENT)

            self.assertEqual(mock_ftp_client.return_value.nlst.call_count, 4)
            self.assertEqual(mock_ftp_client.return_value.connect.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 3)

    def test_check_url_failing_after_retries(self):
        """Test when checking a URL fails after retries"""
        mock_dataset_uri = mock.Mock()
        mock_dataset_uri.uri = 'ftp://foo/bar/baz.nc'
        with mock.patch('geospaas.harvesting.verify_urls.FTPProvider.ftp_client',
                        new_callable=mock.PropertyMock) as mock_ftp_client, \
             mock.patch('time.sleep') as mock_sleep:

            mock_ftp_client.return_value.nlst.side_effect = ConnectionResetError
            provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})

            with self.assertRaises(ConnectionResetError), \
                 self.assertLogs(verify_urls.logger, level=logging.ERROR):
                provider.check_url(mock_dataset_uri)

            self.assertEqual(mock_ftp_client.return_value.nlst.call_count, 5)
            self.assertEqual(mock_ftp_client.return_value.connect.call_count, 4)
            self.assertEqual(mock_sleep.call_count, 4)

    def test_check_all_urls(self):
        """Test that the right URLs are written to the output file"""
        provider = verify_urls.FTPProvider('test', {'url': 'ftp://foo'})
        with mock.patch('geospaas.harvesting.verify_urls.DatasetURI.objects') as mock_manager, \
             mock.patch.object(provider, 'check_url') as mock_check_url, \
             mock.patch.object(provider, 'write_stale_url') as mock_write:

            mock_manager.filter.return_value.iterator.return_value = iter([
                mock.Mock(id=1, uri='ftp://foo/bar/baz1.nc'),
                mock.Mock(id=2, uri='ftp://foo/bar/baz2.nc'),
                mock.Mock(id=3, uri='ftp://foo/bar/baz3.nc'),
            ])

            mock_check_url.side_effect = (verify_urls.ABSENT, verify_urls.PRESENT, 'http_503')

            with self.assertLogs(verify_urls.logger):
                provider.check_all_urls('output.txt')

            self.assertListEqual(mock_write.call_args_list, [
                mock.call('output.txt', verify_urls.ABSENT, 1, 'ftp://foo/bar/baz1.nc'),
                mock.call('output.txt', 'http_503', 3, 'ftp://foo/bar/baz3.nc'),
            ])


class VerifyURLsTestCase(unittest.TestCase):
    """Test the URLs verification module"""

    def test_main_check(self):
        """The correct actions should be launched depending on the CLI
        arguments
        """
        args = mock.Mock()
        args.action = 'check'
        with mock.patch('geospaas.harvesting.verify_urls.parse_cli_arguments', return_value=args), \
                mock.patch('geospaas.harvesting.verify_urls.read_config'), \
                mock.patch('geospaas.harvesting.verify_urls.check_providers') as mock_check, \
                mock.patch('geospaas.harvesting.verify_urls.delete_stale_urls') as mock_delete:

            with self.assertLogs(verify_urls.logger):
                verify_urls.main()
            mock_check.assert_called_once()
            mock_delete.assert_not_called()

    def test_main_delete(self):
        """Test that the delete_stale_urls() function is called when
        the 'delete-stale' argument is given on the CLI
        """
        args = mock.Mock()
        args.action = 'delete-stale'
        with mock.patch('geospaas.harvesting.verify_urls.parse_cli_arguments', return_value=args), \
                mock.patch('geospaas.harvesting.verify_urls.read_config'), \
                mock.patch('geospaas.harvesting.verify_urls.check_providers') as mock_check, \
                mock.patch('geospaas.harvesting.verify_urls.delete_stale_urls') as mock_delete:

            with self.assertLogs(verify_urls.logger):
                verify_urls.main()
            mock_check.assert_not_called()
            mock_delete.assert_called_once()

    def test_parse_cli_arguments_check(self):
        """Test CLI arguments parsing for the check action"""
        with mock.patch('sys.argv',
                        ['verify_urls.py', '-p', '/foo.yml', 'check', '-o', '/bar']):
            self.assertEqual(
                verify_urls.parse_cli_arguments(),
                argparse.Namespace(
                    providers_conf='/foo.yml', action='check', output_directory='/bar'))

    def test_parse_cli_arguments_check_defaults(self):
        """Test CLI arguments parsing for the check action with default
        values
        """
        default_provider_conf = os.path.join(os.path.dirname(verify_urls.__file__), 'check.yml')
        with mock.patch('sys.argv', ['verify_urls.py', 'check']):
            self.assertEqual(
                verify_urls.parse_cli_arguments(),
                argparse.Namespace(
                    providers_conf=default_provider_conf, action='check', output_directory='.'))

    def test_parse_cli_arguments_delete(self):
        """Test CLI arguments parsing for the delete action"""
        with mock.patch('sys.argv',
                        ['verify_urls.py', '-p', '/foo.yml', 'delete-stale', '/bar/baz.txt']):
            self.assertEqual(
                verify_urls.parse_cli_arguments(),
                argparse.Namespace(
                    providers_conf='/foo.yml',
                    action='delete-stale',
                    urls_file='/bar/baz.txt',
                    force=False))

    def test_parse_cli_arguments_delete_force(self):
        """Test CLI arguments parsing for the delete action with the force option"""
        with mock.patch('sys.argv',
                        ['verify_urls.py', '-p', '/foo.yml', 'delete-stale', '/bar/baz.txt', '-f']):
            self.assertEqual(
                verify_urls.parse_cli_arguments(),
                argparse.Namespace(
                    providers_conf='/foo.yml',
                    action='delete-stale',
                    urls_file='/bar/baz.txt',
                    force=True))

    def test_parse_cli_arguments_no_action(self):
        """An error should be raised if no action is specified in the
        CLI arguments
        """
        buffer = io.StringIO()
        with mock.patch('sys.argv', ['verify_urls.py']), \
                mock.patch('sys.stderr', buffer), \
                self.assertRaises(SystemExit):
            verify_urls.parse_cli_arguments()
            self.assertIn(
                'the following arguments are required: action',
                buffer.getvalue())

    def test_parse_cli_arguments_check_wrong_arg(self):
        """An error should be raised if the wrong argument is provided
        to the check action
        """
        buffer = io.StringIO()
        with mock.patch('sys.argv', ['verify_urls.py', 'check', '-f']), \
                mock.patch('sys.stderr', buffer), \
                self.assertRaises(SystemExit):
            verify_urls.parse_cli_arguments()
            self.assertIn('unrecognized arguments: -f', buffer.getvalue())

    def test_parse_cli_arguments_delete_wrong_arg(self):
        """An error should be raised if the wrong argument is provided
        to the delete action
        """
        buffer = io.StringIO()
        with mock.patch('sys.argv', ['verify_urls.py', 'delete-stale', '-o', '/bar']), \
                mock.patch('sys.stderr', buffer), \
                self.assertRaises(SystemExit):
            verify_urls.parse_cli_arguments()
            self.assertIn('unrecognized arguments: -o', buffer.getvalue())

    def test_delete_stale_urls(self):
        """404 URLs should be deleted unless the force option is used
        """
        provider = verify_urls.HTTPProvider('test', {
            'url': 'https://foo',
            'username': 'username',
            'password': 'password',
            'auth_renew': -1
        })
        file_contents = f'{verify_urls.ABSENT} 12 https://foo/bar\nhttp_500 13 https://foo/baz'
        check_url_results = (verify_urls.ABSENT, 'http_500')

        dataset_uris = {12: 'https://foo/bar', 13: 'https://foo/baz'}
        mock_manager = mock.Mock()
        mock_manager.filter.side_effect = lambda id: [mock.Mock(uri=dataset_uris.get(id))]

        with mock.patch('geospaas.harvesting.verify_urls.find_provider', return_value=provider), \
             mock.patch('geospaas.harvesting.verify_urls.DatasetURI.objects', mock_manager):

            # force == False, only the URL that returns 404 must be
            # deleted
            buffer = io.StringIO(file_contents)
            with mock.patch('geospaas.harvesting.verify_urls.open', return_value=buffer), \
                    mock.patch('geospaas.harvesting.verify_urls.HTTPProvider.check_url',
                               side_effect=check_url_results), \
                    mock.patch('geospaas.harvesting.verify_urls.remove_dataset_uri',
                               return_value=(True, True)) as mock_remove:
                self.assertEqual(verify_urls.delete_stale_urls('', {}, force=False), (1, 1))
                self.assertListEqual(
                    [args[0][0].uri for args in mock_remove.call_args_list],
                    ['https://foo/bar'])

            # force == True, both URLs must be deleted
            buffer = io.StringIO(file_contents)
            with mock.patch('geospaas.harvesting.verify_urls.open', return_value=buffer), \
                    mock.patch('geospaas.harvesting.verify_urls.HTTPProvider.check_url',
                               side_effect=check_url_results), \
                    mock.patch('geospaas.harvesting.verify_urls.remove_dataset_uri',
                               return_value=(True, True)) as mock_remove:
                self.assertEqual(verify_urls.delete_stale_urls('', {}, force=True), (2, 2))
                self.assertListEqual(
                    [args[0][0].uri for args in mock_remove.call_args_list],
                    ['https://foo/bar', 'https://foo/baz'])

            # The URI does not exist
            buffer = io.StringIO(file_contents)
            with mock.patch('geospaas.harvesting.verify_urls.open', return_value=buffer):
                mock_manager.filter.side_effect = None
                mock_manager.filter.return_value = []
                with self.assertLogs(verify_urls.logger, level=logging.WARNING):
                    self.assertEqual(verify_urls.delete_stale_urls('', {}, force=False), (0, 0))

    def test_remove_dataset_uri_and_dataset(self):
        """The URI should be removed, as well as the corresponding
        dataset if it does not have anymore URIs
        """
        dataset_uri = mock.Mock()
        dataset_uri.delete.return_value = (1, {'catalog.DatasetURI': 1})
        dataset_uri.dataset.delete.return_value = (1, {'catalog.Dataset': 1})

        # simulate empty queryset
        dataset_uri.dataset.dataseturi_set.all.return_value = []
        self.assertTupleEqual(verify_urls.remove_dataset_uri(dataset_uri), (True, True))
        dataset_uri.delete.assert_called_once_with()
        dataset_uri.dataset.delete.assert_called_once_with()

    def test_remove_dataset_uri_but_not_dataset(self):
        """The URI should be removed, but not the corresponding
        dataset if it has more URIs
        """
        dataset_uri = mock.Mock()
        dataset_uri.delete.return_value = (1, {'catalog.DatasetURI': 1})

        # simulate queryset with one element
        dataset_uri.dataset.dataseturi_set.all.return_value = [mock.Mock()]
        self.assertTupleEqual(verify_urls.remove_dataset_uri(dataset_uri), (True, False))
        dataset_uri.delete.assert_called_once_with()
        dataset_uri.dataset.delete.assert_not_called()

    def test_dataset_uri_and_dataset_not_removed(self):
        """If the URI and/or dataset are not removed,
        remove_dataset_uri() should return booleans indicating so.
        This should not usually happen.
        """
        dataset_uri = mock.Mock()
        dataset_uri.delete.return_value = (0, {'catalog.DatasetURI': 0})
        dataset_uri.dataset.delete.return_value = (0, {'catalog.Dataset': 0})

        # simulate empty queryset
        dataset_uri.dataset.dataseturi_set.all.return_value = []
        self.assertTupleEqual(verify_urls.remove_dataset_uri(dataset_uri), (False, False))
        dataset_uri.delete.assert_called_once_with()
        dataset_uri.dataset.delete.assert_called_once_with()

    def test_find_provider(self):
        """Should return the right provider given a URL"""
        scihub_provider = verify_urls.HTTPProvider('scihub', {
            'url': 'https://scihub.copernicus.eu/',
            'username': 'scihub_user',
            'password': 'scihub_pass',
            'throttle': 0
        })
        podaac_provider = verify_urls.HTTPProvider('podaac', {
            'url': 'https://opendap.jpl.nasa.gov/opendap/',
            'username': 'podaac_user',
            'password': 'podaac_pass',
            'throttle': 0
        })
        providers = [scihub_provider, podaac_provider]

        self.assertIsNone(verify_urls.find_provider('foo.txt', providers))
        self.assertEqual(
            verify_urls.find_provider('scihub_stale_urls_2021-05-25T10:22:27.txt', providers),
            scihub_provider)
        self.assertEqual(
            verify_urls.find_provider('podaac_stale_urls_2021-05-25T10:22:28.txt', providers),
            podaac_provider)

    def test_check_providers(self):
        """Should run URL checks for each provider in a separate
        process. If an exception is raised in one of the sub-processes,
        check_providers() should return False and the traceback of the
        exception should be logged
        """
        providers = [
            verify_urls.HTTPProvider('scihub', {
                'url': 'https://scihub.copernicus.eu/',
                'username': 'scihub_user',
                'password': 'scihub_pass',
                'throttle': 0
            }),
            verify_urls.HTTPProvider('podaac', {
                'url': 'https://opendap.jpl.nasa.gov/opendap/',
                'username': 'podaac_user',
                'password': 'podaac_pass',
                'throttle': 0
            }),
            verify_urls.FTPProvider('rtofs', {
                'url': 'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            }),
        ]

        with mock.patch('concurrent.futures.ProcessPoolExecutor') as mock_pool, \
                mock.patch('geospaas.harvesting.verify_urls.datetime') as mock_datetime, \
                mock.patch('geospaas.harvesting.verify_urls.'
                           'HTTPProvider.check_all_urls') as mock_http_check, \
                mock.patch('geospaas.harvesting.verify_urls.'
                           'FTPProvider.check_all_urls') as mock_ftp_check, \
                mock.patch('concurrent.futures.as_completed', iter):
            mock_executor = mock_pool.return_value.__enter__.return_value
            mock_datetime.now.return_value.strftime.return_value = 'time'
            self.assertTrue(verify_urls.check_providers('foo', providers))
            mock_executor.submit.assert_has_calls((
                mock.call(
                    mock_http_check,
                    os.path.join('foo', 'scihub_stale_urls_time.txt')),
                mock.call(
                    mock_http_check,
                    os.path.join('foo', 'podaac_stale_urls_time.txt')),
                mock.call(
                    mock_ftp_check,
                    os.path.join('foo', 'rtofs_stale_urls_time.txt'))
            ), any_order=True)
            self.assertEqual(len(mock_executor.submit.call_args_list), 3)

            mock_executor.submit.return_value.result.side_effect = AttributeError
            with self.assertLogs(verify_urls.logger, level=logging.ERROR):
                self.assertFalse(verify_urls.check_providers('foo', providers))


    def test_read_config(self):
        """Should read the provider configuration from a YAML file"""
        config = textwrap.dedent('''---
        podaac:
          url: 'https://opendap.jpl.nasa.gov/opendap/'
        scihub:
          url: 'https://scihub.copernicus.eu/'
          username: !ENV 'COPERNICUS_OPEN_HUB_USERNAME'
          password: !ENV 'COPERNICUS_OPEN_HUB_PASSWORD'
        creodias:
          url: 'https://zipper.creodias.eu/'
          username: !ENV 'CREODIAS_USERNAME'
          password: !ENV 'CREODIAS_PASSWORD'
          token_url: 'https://auth.creodias.eu/auth/realms/DIAS/protocol/openid-connect/token'
          client_id: 'CLOUDFERRO_PUBLIC'
          throttle: 1
          auth_renew: 36000
        rtofs:
            url: 'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
          ''')
        environment = {
            'COPERNICUS_OPEN_HUB_USERNAME': 'copernicus_user',
            'COPERNICUS_OPEN_HUB_PASSWORD': 'copernicus_password',
            'CREODIAS_USERNAME': 'creodias_user',
            'CREODIAS_PASSWORD': 'creodias_password',
        }
        # we check that get_auth() is called with the right arguments
        # by replacing its output by its arguments
        with mock.patch('geospaas.harvesting.verify_urls.open', mock.mock_open(read_data=config)), \
                mock.patch('os.environ', environment):
            providers = verify_urls.read_config('foo.yml')

        self.assertListEqual(providers, [
            verify_urls.HTTPProvider('podaac', {
                'url': 'https://opendap.jpl.nasa.gov/opendap/',
            }),
            verify_urls.HTTPProvider('scihub', {
                'url': 'https://scihub.copernicus.eu/',
                'username': 'copernicus_user',
                'password': 'copernicus_password'
            }),
            verify_urls.HTTPProvider('creodias', {
                'url': 'https://zipper.creodias.eu/',
                'username': 'creodias_user',
                'password': 'creodias_password',
                'token_url': 'https://auth.creodias.eu/auth/realms/DIAS/protocol/'
                                'openid-connect/token',
                'client_id': 'CLOUDFERRO_PUBLIC',
                'throttle': 1,
                'auth_renew': 36000
            }),
            verify_urls.FTPProvider('rtofs', {
                'url': 'ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/rtofs/prod/'
            })
        ])

    def test_get_http_provider(self):
        """Test that a HTTPProvider is returned when the url starts
        with 'http'
        """
        self.assertIsInstance(
            verify_urls.get_provider('test', {'url': 'http://foo'}),
            verify_urls.HTTPProvider)
        self.assertIsInstance(
            verify_urls.get_provider('test', {'url': 'https://foo'}),
            verify_urls.HTTPProvider)

    def test_get_ftp_provider(self):
        """Test that a FTPProvider is returned when the url starts
        with 'ftp'
        """
        self.assertIsInstance(
            verify_urls.get_provider('test', {'url': 'ftp://foo'}),
            verify_urls.FTPProvider)

    def test_get_provider_error(self):
        """A ValueError should be raised if no type of provider can be
        chosen
        """
        with self.assertRaises(ValueError):
            verify_urls.get_provider('test', {'url': 'file:///foo/'})

    def test_bounded_thread_pool_executor_init(self):
        """The executor should have a semaphore attribute with an
        initial value equal to the provided queue limit + the number of
        workers
        """
        pool_executor = verify_urls.BoundedThreadPoolExecutor(max_workers=1, queue_limit=1)
        self.assertIsInstance(pool_executor.semaphore, verify_urls.BoundedSemaphore)
        self.assertEqual(pool_executor.semaphore._initial_value, 2)

    def test_bounded_thread_pool_executor_submit(self):
        """This executor should stop adding jobs to its internal queue
        when it hits the limit
        """
        # check that the semaphore is acquired and released in a
        # normal case
        with verify_urls.BoundedThreadPoolExecutor(max_workers=1, queue_limit=1) as bounded_pool:
            bounded_pool.semaphore = mock.Mock()
            bounded_pool.submit(lambda x: x, 1,)
        bounded_pool.semaphore.acquire.assert_called()
        bounded_pool.semaphore.release.assert_called()

        # check that the semaphore is acquired and released when
        # submit() raises an exception
        with mock.patch('concurrent.futures.ThreadPoolExecutor.submit', side_effect=ValueError):
            with verify_urls.BoundedThreadPoolExecutor(
                    max_workers=1, queue_limit=1) as bounded_pool:
                bounded_pool.semaphore = mock.Mock()
                with self.assertRaises(ValueError):
                    bounded_pool.submit(lambda x: x, 1,)
        bounded_pool.semaphore.acquire.assert_called()
        bounded_pool.semaphore.release.assert_called()

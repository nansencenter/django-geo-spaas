"""Unit tests for the geospaas.vocabularies app"""
from unittest.mock import MagicMock, call, patch

import django.db.models
import django.db.utils
from django.core.management import call_command
from django.test import TestCase

from geospaas.vocabularies.managers import VocabularyManager
from geospaas.vocabularies.models import (Keyword, Parameter, validate_parameter, ValidationError)


class VocabulariesTestBase(object):
    """Base class for all vocabularies test cases. Contains mocks set up and common tests."""

    fixtures = ["vocabularies"]
    def setUp(self):
        self.patcher = patch('geospaas.vocabularies.managers.print')
        self.mock_print = self.patcher.start()
        mocked_methods = {}
        for i, vocabulary_name in enumerate(self.model.objects.vocabularies):
            mocked_methods[vocabulary_name] = {
                'get_list': MagicMock(return_value=[]),
                'update': MagicMock(return_value=None)
            }
        methods_patcher = patch.object(self.model.objects, 'vocabularies', mocked_methods)
        methods_patcher.start()
        self.addCleanup(methods_patcher.stop)

    def tearDown(self):
        self.patcher.stop()

    def test_create_from_vocabularies(self):
        """ Test shared with all vocabularies """
        self.model.objects.create_from_vocabularies(force=True)
        self.model.objects.create_from_vocabularies()
        for mocked_methods in self.model.objects.vocabularies.values():
            mocked_methods['get_list'].assert_called()
            mocked_methods['update'].assert_called()
        self.assertIn('Successfully added', self.mock_print.call_args[0][0])

    def _insert_twice(self, attributes):
        """Test that an object of the given model class can't be inserted twice"""
        object1 = self.model(**attributes)
        object2 = self.model(**attributes)

        object1.save()
        object2.save()


class VocabularyManagerTests(TestCase):
    """Tests for the VocabularyManager class"""

    def test_update_and_get_list(self):
        """Test the update_and_get_list() method"""
        vocabulary_manager = VocabularyManager()
        mock_get_list = MagicMock(return_value=[{'foo': 'bar'}, {'Revision': 'baz'}])
        mock_update = MagicMock()

        # test call without force
        self.assertEqual(
            vocabulary_manager.update_and_get_list(mock_get_list, mock_update, False),
            [{'foo': 'bar'}])
        mock_get_list.assert_called_once_with()
        mock_update.assert_not_called()

        mock_get_list.reset_mock()
        mock_update.reset_mock()

        # test call with force and specified version
        self.assertEqual(
            vocabulary_manager.update_and_get_list(
                mock_get_list, mock_update, True, version='9.1.5'),
            [{'foo': 'bar'}])
        mock_get_list.assert_called_once_with()
        mock_update.assert_called_once_with(version='9.1.5')

    def test_create_from_vocabularies(self):
        """Test that create_from_vocabularies() correctly merges the
        lists from pythesint
        """
        manager = VocabularyManager()
        manager.vocabularies = {
            'voc1': {
                'get_list': MagicMock(),
                'update': MagicMock()
            },
            'voc2': {
                'get_list': MagicMock(),
                'update': MagicMock(),
                'get_version': lambda: 'vFoo',
            }
        }

        with patch.object(manager, 'create_instances') as mock_create_instances, \
                patch.object(manager, 'update_and_get_list') as mock_update_and_get_list:
            mock_update_and_get_list.side_effect = [
                [{'standard_name': 'foo'}],
                [{'standard_name': 'foo'}, {'standard_name': 'bar'}]
            ]
            manager.create_from_vocabularies(force=True, versions={'voc1': '9.1.5', 'voc2': '10.3'})
            mock_update_and_get_list.assert_has_calls([
                call(manager.vocabularies['voc1']['get_list'],
                     manager.vocabularies['voc1']['update'],
                     True, version='9.1.5'),
                call(manager.vocabularies['voc2']['get_list'],
                     manager.vocabularies['voc2']['update'],
                     True, version='10.3')
            ])
            mock_create_instances.assert_called_with(
                'voc2', [{'standard_name': 'foo'}, {'standard_name': 'bar'}], 'vFoo')

    def test_get_or_create(self):
        """Test that the model fields are correctly mapped to the GCMD
        entries' fields
        """

        class TestVocabularyManager(VocabularyManager):
            """Manager used for tests"""
            vocabularies = {
                'test_voc': {
                    'get_list': lambda: [
                        {'key1': 'val11', 'key2': 'val12'},
                        {'key1': 'val21', 'key3': 'val22_loooooooong'},
                    ],
                    'update': lambda: None,
                }
            }
            mappings = [
                {'key1': 'key1', 'key2': 'key2'},
                {'key1': 'key1', 'key2': 'key3'},
            ]

        class TestModel(django.db.models.Model):
            """Model used for tests"""
            key1 = django.db.models.CharField(max_length=10)
            key2 = django.db.models.CharField(max_length=10)
            objects = TestVocabularyManager()

        with patch('geospaas.vocabularies.managers.models.Manager.get_or_create',
                   return_value=(True, None)) as mock_get_or_create, \
             patch('builtins.print'):
            manager = TestModel.objects
            manager.create_from_vocabularies()
            mock_get_or_create.assert_has_calls((
                call(version=None, kind='test_voc', data={'key1': 'val11', 'key2': 'val12'}),
                call(version=None, kind='test_voc', data={'key1': 'val21',
                                                          'key3': 'val22_loooooooong'})))


class KeywordTests(VocabulariesTestBase, TestCase):
    """Tests """
    model = Keyword

    def test_str(self):
        """Test string representation of a Keyword object"""
        self.assertEqual(
            str(Keyword(version='v1', kind='test', data={'foo': 'bar'})),
            'Keyword object (None)')
        self.assertEqual(
            str(Keyword(version='v1', kind='test', data={'foo': 'bar', 'Short_Name': 'baz'})),
            'baz')


class ParameterTests(VocabulariesTestBase, TestCase):
    """Unit tests for the Parameter model"""

    model = Parameter

    def test_unique_constraint(self):
        """Check that the same Parameter can't be inserted twice"""
        with self.assertRaises(django.db.utils.IntegrityError):
            self._insert_twice({
                'version': '1.0',
                'kind': 'test',
                'data': {'standard_name': 'test', 'short_name': 'test', 'units': 'test'},
                'gcmd_science_keyword': Keyword.objects.first(),
            })

    def test_get_by_natural_key(self):
        """Test getting a Parameter by natural key"""
        self.assertEqual(
            Parameter.objects.get_by_natural_key('baz'),
            Parameter.objects.get(id=1))

    def test_validate_parameter(self):
        """Test validation of the data field"""
        self.assertIsNone(validate_parameter({'standard_name': 'foo'}))
        with self.assertRaises(ValidationError):
            validate_parameter('foo')

    def test_str(self):
        """Test getting the string representation of a Parameter"""
        self.assertEqual(
            str(Parameter(version='v1', kind='test', data={'standard_name': 'foo'})), 'foo')

    def test_natural_key(self):
        """Test getting the natural key of a Parameter"""
        self.assertEqual(
            Parameter(version='v1', kind='test', data={'standard_name': 'foo'}).natural_key(),
            'foo')


class CommandsTests(TestCase):
    """Unit tests for the custom commands of the vocabularies app"""

    def setUp(self):
        managers = ('geospaas.vocabularies.managers.KeywordManager',
                    'geospaas.vocabularies.managers.ParameterManager')
        self.mocks_create_from_voc = []
        for manager in managers:
            patcher = patch(f"{manager}.create_from_vocabularies")
            self.mocks_create_from_voc.append(patcher.start())
            self.addCleanup(patcher.stop)

    def test_command_update_vocabularies(self):
        """Check that the command does not update the vocabularies if they are present"""
        call_command('update_vocabularies')
        for mock_create_from_voc in self.mocks_create_from_voc:
            mock_create_from_voc.assert_called_once()
            _, kwargs = mock_create_from_voc.call_args_list[0]
            self.assertFalse(kwargs['force'])
            self.assertIsNone(kwargs['versions'])

    def test_command_update_vocabularies_force(self):
        """
        Check that the command updates the vocabularies even if they are present when --force is
        specified
        """
        call_command('update_vocabularies', '--force')
        for mock_create_from_voc in self.mocks_create_from_voc:
            mock_create_from_voc.assert_called_once()
            _, kwargs = mock_create_from_voc.call_args_list[0]
            self.assertTrue(kwargs['force'])
            self.assertIsNone(kwargs['versions'])

    def test_command_update_vocabularies_versions(self):
        """Check that the command updates the vocabularies with the
        provided versions
        """
        call_command('update_vocabularies', '--versions', 'foo=1.0.0', 'bar=2.0.0')
        for mock_create_from_voc in self.mocks_create_from_voc:
            mock_create_from_voc.assert_called_once()
            _, kwargs = mock_create_from_voc.call_args_list[0]
            self.assertDictEqual(kwargs['versions'], {'foo': '1.0.0', 'bar': '2.0.0'})

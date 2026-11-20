"""Tests for the Django apps"""
import django.apps
import django.test

import geospaas.processing.apps

class GeospaasProcessingAppTestCase(django.test.SimpleTestCase):
    """Test the geospaas.processing app"""
    def test_app_name(self):
        """Test the app has the correct name"""
        app_name = 'geospaas.processing'
        self.assertEqual(geospaas.processing.apps.GeospaasProcessingConfig.name, app_name)

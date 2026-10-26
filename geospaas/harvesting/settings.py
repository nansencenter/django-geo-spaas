"""Django settings"""
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'fake-key')

INSTALLED_APPS = [
    'geospaas.catalog',
    'geospaas.vocabularies',
    'geospaas.harvesting',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': os.getenv('GEOSPAAS_DB_HOST', 'localhost'),
        'PORT': os.getenv('GEOSPAAS_DB_PORT', '5432'),
        'NAME': os.getenv('GEOSPAAS_DB_NAME', 'geodjango'),
        'USER': os.getenv('GEOSPAAS_DB_USER', 'geodjango'),
        'PASSWORD': os.getenv('GEOSPAAS_DB_PASSWORD'),
        'CONN_MAX_AGE': int(os.getenv('GEOSPAAS_CONN_MAX_AGE', '600')),
        'CONN_HEALTH_CHECKS': True,
    }
}

if os.getenv('GEOSPAAS_DISABLE_SERVER_SIDE_CURSORS', 'false').lower() == 'true':
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True  # pragma: no cover

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

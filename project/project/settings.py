"""
Django settings for project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),
    os.pardir))
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

# ./manage.py collectstatic will put the static files (also from the apps)
# here:
STATIC_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "static")
# uploaded media should be put here (change in production)
MEDIA_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "media")
# Downloaded datasets should be stored here (change in production)
DOWNLOAD_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "downloads")
# Derived parameters should be stored in netcdf's here (change in production)
PRODUCT_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "products")

if not os.path.exists(os.path.join(PACKAGE_ROOT, "site_media")):
    os.mkdir(os.path.join(PACKAGE_ROOT, "site_media"))
if not os.path.exists(STATIC_ROOT):
    os.mkdir(STATIC_ROOT)
if not os.path.exists(MEDIA_ROOT):
    os.mkdir(MEDIA_ROOT)
if not os.path.exists(DOWNLOAD_ROOT):
    os.mkdir(DOWNLOAD_ROOT)
if not os.path.exists(PRODUCT_ROOT):
    os.mkdir(PRODUCT_ROOT)

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PACKAGE_ROOT, "static"),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/site_media/static/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/site_media/media/'

LOGIN_URL = '/helpdesk/login/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'n377^y0m&n7%-(g+o37(7fkkf5@nui_r-3msk_mkl3sp=85319'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
]

TEMPLATE_DIRS = [
    os.path.join(PACKAGE_ROOT, "templates"),
]

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_forms_bootstrap',
    'leaflet',
    'nansencloud.vocabularies',
    'nansencloud.catalog',
    'nansencloud.nansat_ingestor',
    'nansencloud.viewer',
    #'nansencloud.processing_hab',
    #'nansencloud.processing_sar', # not sure if we should split or not...
    #'nansencloud.processing_sar_nrcs',
    'nansencloud.processing_sar_doppler',
    #'nansencloud.processing_ais',
    #'nansencloud.proc',
    #'nansencloud.noaa_ndbc',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'project.urls'

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(PROJECT_ROOT,  'geodjango.db'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (30.0, 0.0),
    'DEFAULT_ZOOM': 1,
    'MIN_ZOOM': 1,
    'MAX_ZOOM': 10,
    'RESET_VIEW': False,
    'SRID': 3857,
    'PLUGINS': {
        'forms': {
            'auto-include': True
        }
    }
}

PROCESSING_HAB = {
    'output_directory': os.path.join(MEDIA_ROOT, 'hab/products'),
    'http_address': os.path.join(MEDIA_URL, 'hab/products'),
}

INSTALLED_APPS = [
    'geospaas.catalog',
    'geospaas.vocabularies',
    'geospaas.nansat_ingestor',
]

SECRET_KEY = 'kljhfek@=w^dnto^3hqqm)(3npeag6d2q3a@swxhj&)4qkv(#b'

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': 'test.db',
    }
}

USE_TZ = True


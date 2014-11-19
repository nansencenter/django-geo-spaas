POSTGIS_VERSION = (1, 5, 3)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'geodjango',
        'USER': 'opengeo',
        'PASSWORD': 'open2012geo',
        'HOST': '10.47.20.19',
        'PORT': '5432',
        }
    }

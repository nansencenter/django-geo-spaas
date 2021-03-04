Django-Geo-SPaaS - GeoDjango Apps for satellite data management
===========================================================
[![Build Status](https://travis-ci.org/nansencenter/django-geo-spaas.svg?branch=master)](https://travis-ci.org/nansencenter/django-geo-spaas)
[![Coverage Status](https://coveralls.io/repos/github/nansencenter/django-geo-spaas/badge.svg?branch=master)](https://coveralls.io/github/nansencenter/django-geo-spaas)
[![DOI](https://zenodo.org/badge/84077597.svg)](https://zenodo.org/badge/latestdoi/84077597)


How to use Docker for development of Django-Geo-SPaaS
-----------------
1. [Install Docker](https://docs.docker.com/install/)
2. Clone `django-geo-spaas` and change into that directory
3. Run `./build_container.sh`. That will do the following:
  * build a Docker image with Nansat, Django and Django-Geo-SPaaS installed
  * create a project directory `project` in the current dir
  * create the database and update vocabularies
  * create a container with name `geospaas` with the current dir mounted to `/src`. Thus the container sees all changes you
  do to the geospaas code.
4. Run `docker start -i geospaas`. That will launch `bash` inside the `geospaas` containter.
From bash you can launch: `python project/manage.py shell`.
5. If you want to mount more directories, you can run the following command:
```
docker create -it --name=geospaas \
    -v `pwd`:/src \
    -v /input/dir/on/host:/path/to/dir/in/container \
    geospaas
```
And then run `docker start -i geospaas` to go into the container and have access to commands.
6. Alretrnatively you can start the container in background:
`docker start geospaas`
and then execute commands in the runnning container:
`docker exec -i geospaas project/manage.py shell`

How to use Docker for running Django-Geo-SPaaS
-----------------
If you already have a project directory or if you are working on another app you can use the
existing Docker image with Django-Geo-SPaaS. The image is already uploaded to Docker Hub,
so no above steps are necessary. The workflow can be the following:
1. Create a container with necessary directories mounted
2. Start container in background
3. Run Django commands from your host:
```
# create container named myapp from Docker image geospaas
docker create -it --name=myapp \
    -v /host/dir/myapp:/src \
    -v /data/dir:/data \
    nansencenter/geospaas

# start container in background
docker start myapp

# create project dir in /host/dir/myapp
docker exec myapp django-admin startproject myproject

# update settings.py
```

```
INSTALLED_APPS = [
    ...
    'django.contrib.gis',
    'leaflet',
    'django_forms_bootstrap',
    'geospaas.base_viewer',
    'geospaas.catalog',
    'geospaas.vocabularies',
    'myproject',
]

...

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(BASE_DIR, 'geodjango.db'),
    }
}
```

```
# update urls.py
```

```
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tests/', include('geospaas.base_viewer.urls')),
]
```

```
# migrate database schema
docker exec myapp /src/myproject/manage.py migrate

# update vocabularies
docker exec myapp /src/myproject/manage.py update_vocabularies
```

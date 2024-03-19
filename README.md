# Django-Geo-SPaaS - GeoDjango Apps for satellite data management
[![Unit tests and build](https://github.com/nansencenter/django-geo-spaas/actions/workflows/ci.yml/badge.svg)](https://github.com/nansencenter/django-geo-spaas/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/nansencenter/django-geo-spaas/badge.svg?branch=master)](https://coveralls.io/github/nansencenter/django-geo-spaas)
[![DOI](https://zenodo.org/badge/84077597.svg)](https://zenodo.org/badge/latestdoi/84077597)


## About

GeoSPaaS is a set of Python tools meant to help scientists deal with Earth Observation data.
django-geo-spaas is the core of GeoSPaaS. It is composed of several
[GeoDjango](https://docs.djangoproject.com/en/5.0/ref/contrib/gis/) apps which provide basic
functionalities:
- `geospaas.catalog`: defines the structure of GeoSPaaS's catalog, which is used to store metadata
  about Earth Observation datasets. This is the core around which all GeoSPaaS functionalities are
  built.
- `geospaas.vocabularies`: defines a structured way to assign properties to the datasets in the
  catalog. Based on and compatible with the
  [GCMD standard](https://www.earthdata.nasa.gov/learn/find-data/idn/gcmd-keywords).
- `geospaas.base_viewer`: a basic web page which allows to view the contents of the catalog.
- `geospaas.nansat_ingestor`: data ingester based on 
  [Nansat](https://github.com/nansencenter/nansat). Can be used to populate a catalog. The preferred
  tool for this is now 
  [django-geo-spaas-harvesting](https://github.com/nansencenter/django-geo-spaas-harvesting).
- `geospaas.export_DIF`: app for exporting metadata to GCMD DIF format.

## Usage

To make use of `django-geo-spaas`, you need to install the apps in a GeoDjango project.
To set up such a project, you can follow the instructions here:
https://docs.djangoproject.com/en/5.0/ref/contrib/gis/tutorial/.

You can also go through the workshops in the following repository to learn more about GeoSPaaS and
see some practical uses: https://github.com/nansencenter/geospaas-workshops.

## Using Docker

Docker can be used to set up a GeoSPaaS project more easily.  
You will find instructions below for a basic set-up.

### How to use Docker for development of Django-Geo-SPaaS

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

### How to use Docker for running Django-Geo-SPaaS

If you already have a project directory or if you are working on another app you can use the
existing Docker image with Django-Geo-SPaaS. The image is already uploaded to Docker Hub,
so no above steps are necessary. The workflow can be the following:
1. Create a container with necessary directories mounted
2. Start container in background
3. Run Django commands from your host:
```
# create container named myapp from Docker image geospaas
docker run -it --rm --name=myapp \
    -v /host/dir/myapp:/src \
    -v /data/dir:/data \
    nansencenter/geospaas

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
    'geospaas.nansat_ingestor',
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

# ingest metadata
docker exec -w /src/myproject myapp ./manage.py ingest /data/myfiles*.nc
```

## How to add new data to a GeoSPaaS catalog

The [django-geo-spaas-harvesting](https://github.com/nansencenter/django-geo-spaas-harvesting)
app can be used to populate a GeoSPaaS catalog.

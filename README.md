Django-Geo-SPaaS - GeoDjango Apps for satellite data management
===========================================================
[![Build Status](https://travis-ci.org/nansencenter/django-geo-spaas.svg?branch=master)](https://travis-ci.org/nansencenter/django-geo-spaas)
[![Coverage Status](https://coveralls.io/repos/github/nansencenter/django-geo-spaas/badge.svg?branch=master)](https://coveralls.io/github/nansencenter/django-geo-spaas)

How to add new data to Geo-SPaaS catalog
----------------------------------------
Install geo-spaas-vagrant:
```
  git clone https://github.com/nansencenter/geo-spaas-vagrant
  cd geo-spaas-vagrant
  vagrant up geospaas_core
```
Connect to the virtual machine and use GeoSPaaS
```
  vagrant ssh geospaas_core
  cd django-geo-spaas/project
  ./manage.py ingest name_of_your_file
```

How to use Docker for development of Django-Geo-SPaaS
-----------------
1. [Install Docker](https://docs.docker.com/install/)
2. Clone `django-geo-spaas` and change into that directory
3. Run `./build_container.sh`. That will do the following:
  * build a Docker image with Nansat and Django installed
  * Dockerfile also installs geospaas into /opt/geospaas and links from site-pakages
  * create a project directory `project` in the current dir
  * create the database and update vocabularies
  * create a container with name `geospaas` with the current dir mounted to `/src` and
  `geospaas` in the current dir mounted to `/opt/geospaas`. Thus the container sees all changes you
  do to the geospaas code.
4. Run `docker start -i geospaas`. That will launch `bash` inside the `geospaas` containter.
From bash you can launch: `python project/manage.py shell`.
5. If you want to mount more directories, you can run the following command:
```
docker create -it --name=geospaas \
    -v `pwd`:/src \
    -v `pwd`/geospaas:/opt/geospaas \
    -v /input/dir/on/host:/path/to/dir/in/container \
    geospaas
```
And then run `docker start -i geospaas` to go into the container and have access to commands.
6. Alretrnatively you can start the container in background:
`docker start geospaas`
and then execute commands in the runnning container:
`docker exec geospaas project/manage.py shell`

How to use Docker for running Django-Geo-SPaaS
-----------------
If you already have a project directory or if you are working on another app you can use the
existing Docker image with Django-Geo-SPaaS. The workflow can be the following:
1. Create a containter with necessary directories mounted
2. Start container in background
3. Run Django commands from your host:
```
# create container named myapp from Docker image geospaas
docker create -it --name=myapp \
    -v /host/dir/myapp:/src \
    -v /data/dir:/data \
    geospaas

# start container in background
docker start myapp

# create project dir in /host/dir/myapp
docker exec myapp django-admin startproject myproject

# update settings.py and urls.py to use Geo-Django (see tests/settings.py for example)
# don;t forget to set correct name of the project and add your app to the settings.py

# migrate database schema
docker exec myapp /src/myproject/manage.py migrate

# update vocabularies
docker exec myapp /src/myproject/manage.py update_vocabularies

# ingest metadata
docker exec -w /src/myproject myapp ./manage.py ingest /data/myfiles*.nc
```

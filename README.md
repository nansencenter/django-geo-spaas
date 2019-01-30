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
2. Clone `django-geo-spaas`
3. Run `./build_container.sh`. That will do the following:
  * build a Docker image with Nanat, Django and Geo-SPaaS installed
  * create a project directory `project` in the current dir
  * create the database and update vocabularies
  * create a container with name `geospaas` with the current dir mounted to `/code`
4. Run `docker start -i geospaas`. That will launch `bash` inside the `geospaas` containter.
From bash you can launch: `python project/manage.py shell`.
5. If you want to mount more directories, you can run the following command:
```
docker create -it --name=geospaas \
    -v `pwd`:/code geospaas \
    -v /input/dir/on/host:/path/to/dir/in/container \
    geospaas
```
And then `docker start -i geospaas`

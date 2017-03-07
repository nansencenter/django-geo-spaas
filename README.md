Django-Geo-SPaaS - GeoDjango Apps for satellite data management
===========================================================

How to add new data to Geo-SPaaS catalog
----------------------------------------
1. Install geo-spaas-vagrant:
 git clone https://github.com/nansencenter/geo-spaas-vagrant
 cd geo-spaas-vagrant
 vagrant up geospaas_core

2. Connect to the virtual machine and use GeoSPaaS
 vagrant ssh geospaas_core
 cd django-geo-spaas/project
 ./manage.py ingest name_of_your_file

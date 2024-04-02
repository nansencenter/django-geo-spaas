=========
Ecosystem
=========

``django-geo-spaas`` is one application in the GeoSPaaS ecosystem.
Other GeoSPaaS applications provide additional functionalities.

Nansat
======

Nansat is a scientist friendly Python toolbox for processing 2D satellite earth observation data.

| The documentation is available here: https://nansat.readthedocs.io/en/latest/
| The source is available here: https://github.com/nansencenter/nansat/

django-geo-spaas-harvesting
===========================

``django-geo-spaas-harvesting`` is a Django application based on ``django-geo-spaas``.
It can fetch metadata from a variety of providers to populate a GeoSPaaS catalog database.

More information can be found in the source repository:
https://github.com/nansencenter/django-geo-spaas-harvesting

django-geo-spaas-processing
===========================

``django-geo-spaas-processing`` is a Django application based on ``django-geo-spaas``.
It provides tools to deal with the data referenced in a GeoSPaaS catalog database.
For example, it can download the referenced datasets and convert them to formats suited to'
visualisation.

The actions can be run directly or asynchronously as
`Celery <https://docs.celeryq.dev/en/stable/>`_ tasks.

More information can be found in the source repository:
https://github.com/nansencenter/django-geo-spaas-processing

django-geo-spaas-rest-api
=========================

``django-geo-spaas-rest-api`` is a Django application based on the
`Django REST framework <https://www.django-rest-framework.org/>`_.

It exposes a REST API that can be used to search through a GeoSPaaS catalog database and execute
asynchronous tasks available in ``django-geo-spaas-processing``.

More information can be found in the source repository:
https://github.com/nansencenter/django-geo-spaas-rest-api

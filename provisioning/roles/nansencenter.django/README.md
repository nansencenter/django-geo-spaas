nansencenter.django
=========

[![Build Status](https://travis-ci.org/nansencenter/ansible-role-django.svg?branch=master)](https://travis-ci.org/nansencenter/ansible-role-django)

Initialize Django project for GeoSPaaS

Requirements
------------
See [meta/main.yml](meta/main.yml)

Role Variables
--------------
```yml
django_project_home: # Home directory of Django project
django_project_name: # Name of Django project
django_env_name: # Name of anaconda environment
django_conda_dir: # Directory for anaconda environment
django_dirs: # Names and location of directories for satellite products
django_apps: # Name of Django apps to add to 'settings.py'
django_urlpatterns: # Urls to add to 'urls.py'
django_pip_pkgs: # Packages for installations with PIP
```

Dependencies
------------

See [meta/main.yml](meta/main.yml)


Example Playbook
----------------

```yml
---
- hosts: geospaas
  roles:
    - role: nansencenter.django
      django_project_home: '/opt'
      django_project_name: 'project'
      django_env_name: 'py3django'
      django_conda_dir: '/opt/anaconda'
      django_apps:
        - django_forms_bootstrap
        - leaflet
      django_pip_pkgs:
        - django-forms-bootstrap
        - django-leaflet
```

License
-------

GPLv3

Author Information
------------------

Anton Korosov, anton.korosov@nersc.no
Nansen Environmental and Remote Sensing Center, https://github.com/nansencenter/

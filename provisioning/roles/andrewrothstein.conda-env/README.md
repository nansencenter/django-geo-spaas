andrewrothstein.conda-env
=========
[![Build Status](https://travis-ci.org/andrewrothstein/ansible-conda-env.svg?branch=master)](https://travis-ci.org/andrewrothstein/ansible-conda-env)

Creates a named [Conda](http://conda.pydata.org/docs/index.html) environment.

Requirements
------------

Assumes you have installed either Anaconda or Miniconda.

See [meta/main.yml](meta/main.yml)

Role Variables
--------------

See [defaults/main.yml](defaults/main.yml)

Dependencies
------------

See [meta/main.yml](meta/main.yml)

Example Playbook
----------------

```yml
- hosts: servers
  roles:
    - role: andrewrothstein.conda-env
	  conda_env_name: my-environment
	  conda_env_environment: my-environment.yml
```

License
-------

MIT

Author Information
------------------

Andrew Rothstein <andrew.rothstein@gmail.com>

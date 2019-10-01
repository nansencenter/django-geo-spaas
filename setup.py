#-------------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:       Morten Wergeland Hansen
# Modified:
#
# Created:
# Last modified:
# Copyright:    (c) NERSC
# License:
#-------------------------------------------------------------------------------
from setuptools import setup, find_packages
import sys

install_requires = []

setup(name='django-geo-spaas',
      version=0.1,
      description='Geo-Scientific Platform as a Service',
      zip_safe=False,
      author='Morten W. Hansen, Anton Korosov',
      author_email='mortenh@nersc.no, antonk@nersc.no',
      url='https://github.com/nansencenter/django-geo-spaas',
      download_url='https://github.com/nansencenter/django-geo-spaas/archive/master.zip',
      packages = find_packages(),
      include_package_data=True,
      install_requires = install_requires,
      test_suite='runtests.runtests',
      classifiers = ['Development Status :: 0 - Beta',
                     'Environment :: Web Environment',
                     'Framework :: Django',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: Utilities'],
      )

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

setup(
    name='django-geo-spaas',
    version='1.0.1',
    description='Geo-Scientific Platform as a Service',
    zip_safe=False,
    author='Morten W. Hansen, Anton Korosov, Artem Moiseev, Jeong-Won Park, Adrien Perrin',
    author_email='anton.korosov@nersc.no',
    url='https://github.com/nansencenter/django-geo-spaas',
    download_url='https://github.com/nansencenter/django-geo-spaas/archive/master.zip',
    packages = find_packages(),
    include_package_data=True,
    install_requires = install_requires,
    test_suite='runtests.runtests',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)

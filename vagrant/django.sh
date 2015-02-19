sudo pip install Django
sudo pip install django-forms-bootstrap
sudo pip install django-leaflet


# install python-sqlite
# https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/spatialite/#pysqlite2
wget https://pypi.python.org/packages/source/p/pysqlite/pysqlite-2.6.3.tar.gz
tar -xzvf pysqlite-2.6.3.tar.gz
cd pysqlite-2.6.3
# update setup.cfg
echo '[build_ext]' > setup.cfg
echo '#define=' >> setup.cfg
echo 'include_dirs=/usr/local/include' >> setup.cfg
echo 'library_dirs=/usr/local/lib' >> setup.cfg
echo 'libraries=sqlite3' >> setup.cfg
echo '#define=SQLITE_OMIT_LOAD_EXTENSION' >> setup.cfg
sudo python setup.py install


export NUMTHREADS=2

cd /vagrant
if [ ! -f gdal-1.11.1.tar.gz ]; then
    wget http://download.osgeo.org/gdal/1.11.1/gdal-1.11.1.tar.gz
fi
tar -xzvf gdal-1.11.1.tar.gz
cd gdal-1.11.1

#  --with-ecw=/usr/local --with-mrsid=/usr/local --with-mrsid-lidar=/usr/local --with-fgdb=/usr/local
./configure  --prefix=/usr --without-libtool --enable-debug --with-jpeg12 \
            --with-perl --with-python --with-poppler \
            --with-podofo --with-spatialite --with-java --with-mdb \
            --with-jvm-lib-add-rpath --with-epsilon --with-gta \
            --with-mysql --with-liblzma --with-webp --with-libkml \
            --with-openjpeg=/usr/local --with-armadillo \
            --with-geos=yes --with-dods-root=/usr


make -j $NUMTHREADS
cd apps
make test_ogrsf
cd ..

# A previous version of GDAL has been installed by PostGIS
sudo rm -f /usr/lib/libgdal.so*
sudo make install
sudo ldconfig
# not sure why we need to do that
sudo cp -r /usr/lib/python2.7/site-packages/*  /usr/lib/python2.7/dist-packages/

cd

# install pip and upgrade
sudo apt-get install python-pip -y
sudo pip install pip --upgrade

# needed for building scipy
sudo apt-get install liblapack-dev libatlas-dev -y
sudo apt-get install gfortran  -y
#sudo pip install py-dateutil
#sudo pip install pyparsing

# install scientific python tools
sudo pip install ipython
sudo pip install numpy --upgrade
sudo pip install scipy
sudo pip install pillow
sudo pip install netCDF
sudo pip install scikit-learn

# for ipython notebook
sudo pip install pyzmq
sudo pip install jinja2
sudo pip install tornado

# for debugging and testing
sudo pip install ipdb
sudo pip install nose
sudo pip install coverage

# download things non installable automatically into tmp

# matplotlib
cd /vagrant
if [ ! -f matplotlib-1.4.2.tar.gz ]; then
    wget http://downloads.sourceforge.net/project/matplotlib/matplotlib/matplotlib-1.4.2/matplotlib-1.4.2.tar.gz
fi
cd
tar -zxvf /vagrant/matplotlib-1.4.2.tar.gz
cd matplotlib-1.4.2
sudo python setup.py install
cd

# basemap
cd /vagrant
if [ ! -f basemap-1.0.7.tar.gz ]; then
    wget http://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.7/basemap-1.0.7.tar.gz
fi
cd
tar -zxvf /vagrant/basemap-1.0.7.tar.gz
cd basemap-1.0.7/geos-3.3.3
export GEOS_DIR=/usr/local
./configure --prefix=$GEOS_DIR
make
sudo make install
ldconfig
cd ..
sudo python setup.py install
cd

sudo pip install Django
sudo pip install django-forms-bootstrap
sudo pip install django-leaflet

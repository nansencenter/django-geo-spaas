if [ ! -d "/home/vagrant/python" ]; then
    mkdir /home/vagrant/python
fi
if [ ! -d "/home/vagrant/python/nansat" ]; then
    cd /home/vagrant/python
    git clone https://github.com/nansencenter/nansat
else
    cd nansat
    git pull
fi
git clone https://github.com/nansencenter/openwind
git clone https://github.com/nansencenter/nansen-cloud

# checkout develop branches
cd /home/vagrant/python/OpenWind
git checkout develop
cd /home/vagrant/python/nansen-cloud
git checkout develop
cd /home/vagrant/python/nansat
git checkout develop

# install nansat in-place - this allows editing directly on the source with no
# need to reinstall unless the pixel functions are modified
sudo python setup.py build_ext --inplace

# symlink packages from python dist-packages
cd /usr/local/lib/python2.7/dist-packages/
sudo ln -s /home/vagrant/python/nansat/nansat
sudo ln -s /home/vagrant/python/nansat/end2endtests
sudo ln -s /home/vagrant/python/nansen-cloud/nansencloud
sudo ln -s /home/vagrant/python/OpenWind/openwind

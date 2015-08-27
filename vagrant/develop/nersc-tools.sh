# THIS IS THE INSTALL SCRIPT FOR DEVELOP MODE
if [ ! -d "/home/vagrant/python" ]; then
    mkdir /home/vagrant/python
fi
if [ ! -d "/home/vagrant/python/nansat" ]; then
    cd /home/vagrant/python
    git clone https://github.com/nansencenter/nansat
    cd /home/vagrant/python/nansat
    git checkout develop
    # install nansat in-place - this allows editing directly on the source with
    # no need to reinstall unless the pixel functions are modified
    sudo python setup.py build_ext --inplace
fi
if [ ! -d "/home/vagrant/python/openwind" ]; then
    cd /home/vagrant/python
    git clone https://github.com/nansencenter/openwind
    cd /home/vagrant/python/openwind
    git checkout develop
fi
if [ ! -d "/home/vagrant/python/nansen-cloud" ]; then
    cd /home/vagrant/python
    git clone https://github.com/nansencenter/nansen-cloud
    cd /home/vagrant/python/nansen-cloud
    git checkout develop
fi


# symlink packages from python dist-packages
cd /usr/local/lib/python2.7/dist-packages/
if [ ! -L "nansat" ]; then
    sudo ln -s /home/vagrant/python/nansat/nansat
fi
if [ ! -L "end2endtests" ]; then
    sudo ln -s /home/vagrant/python/nansat/end2endtests
fi
if [ ! -L "nansencloud" ]; then
    sudo ln -s /home/vagrant/python/nansen-cloud/nansencloud
fi
if [ ! -L "openwind" ]; then
    sudo ln -s /home/vagrant/python/openwind/openwind
fi

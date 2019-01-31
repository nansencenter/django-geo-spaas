# Initialize from docker image with Python, libraries and Nansat
FROM akorosov/nansat:latest

# Default values of user and group IDs.
# That should be changed to the IDs of the actual user and group on the host system in the script
# for building the container. For example:
# docker build -t geospaas --build-arg DUID=12345 --build-arg DGID=54321 .
# where 12345 and 54321 are user and group ID on a host system
ARG DUID=1000
ARG DGID=1000

# update user with custom UID and GID
RUN groupadd user -g $DGID \
&&  useradd -m -s /bin/bash -N -u $DUID -g $DGID user \
&&  echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/user/.bashrc \
&&  echo "conda activate base" >> /home/user/.bashrc \
&&  echo "export PYTHONPATH=/django-geo-spaas" >> /home/user/.bashrc \
&&  echo "alias ll='ls -lh'" >> /home/user/.bashrc

ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    django \
    django-forms-bootstrap \
    django-leaflet

# Install Geo-SPaaS
COPY . /django-geo-spaas
#WORKDIR /django-geo-spaas
#RUN python setup.py install
#WORKDIR /code
USER user

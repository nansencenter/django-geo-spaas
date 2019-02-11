# Initialize from docker image with Python, libraries and Nansat
FROM akorosov/nansat:latest

ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    django \
    django-forms-bootstrap \
    django-leaflet

# add user with custom UID and GID and configure environment
# NB! Relevant for Linux users only
# Default values of user and group IDs.
# That should be changed to the IDs of the actual user and group on the host system in the script
# for building the container. For example:
# docker build -t geospaas --build-arg DUID=12345 --build-arg DGID=54321 .
# where 12345 and 54321 are user and group ID on a host system
ARG DUID=1000
ARG DGID=1000
RUN groupadd user -g $DGID \
&&  useradd -m -s /bin/bash -N -u $DUID -g $DGID user \
&&  echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/user/.bashrc \
&&  echo "conda activate base" >> /home/user/.bashrc \
&&  ln -s /opt/geospaas /opt/conda/lib/python3.7/site-packages/geospaas \
&&  echo "alias ll='ls -lh'" >> /home/user/.bashrc

# install Geo-SPaaS into /opt/django-geo-spaas
COPY geospaas /opt/geospaas
USER user
WORKDIR /src

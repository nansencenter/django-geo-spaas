# Initialize from docker image with Python, libraries and Nansat
ARG BASE_IMAGE='nansencenter/nansat:latest'
FROM ${BASE_IMAGE}
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN apt update \
&&  apt install -y \
    # psycopg2 dependencies
    g++ \
    libpq5 \
    libpq-dev \
&&  pip install \
    bs4 \
    coverage \
    django==3.0.6 \
    django-forms-bootstrap==3.1.0 \
    django-leaflet==0.26.0 \
    psycopg2==2.8.4 \
    thredds_crawler==1.5.4 \
&&  apt remove -y g++ && apt autoremove -y \
&&  apt clean && rm -rf /var/lib/apt/lists/* \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
COPY MANIFEST.in /tmp/
WORKDIR /tmp
RUN python setup.py install \
&&  rm -r geospaas setup.py MANIFEST.in

WORKDIR /src

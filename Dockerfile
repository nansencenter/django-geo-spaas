# Initialize from docker image with Python, libraries and Nansat
ARG BASE_IMAGE='nansencenter/nansat:latest'
FROM ${BASE_IMAGE} as base
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
    django==3.2 \
    django-forms-bootstrap \
    django-leaflet \
    psycopg2 \
    thredds_crawler \
&&  apt remove -y g++ && apt autoremove -y \
&&  apt clean && rm -rf /var/lib/apt/lists/* \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

FROM base as full

ARG DJANGO_GEO_SPAAS_RELEASE '0.0.0dev'
# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
COPY MANIFEST.in /tmp/
WORKDIR /tmp
RUN python setup.py install \
&&  rm -r geospaas setup.py MANIFEST.in

WORKDIR /src

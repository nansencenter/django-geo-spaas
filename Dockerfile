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
    django-forms-bootstrap==3.1.0 \
    django-leaflet==0.28.2 \
    psycopg2==2.9.3 \
    thredds_crawler==1.5.4 \
&&  apt remove -y g++ && apt autoremove -y \
&&  apt clean && rm -rf /var/lib/apt/lists/* \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

FROM base as full

# install Geo-SPaaS
COPY . /tmp/geospaas/
RUN pip install /tmp/geospaas && \
    rm -rf /tmp/geospaas

WORKDIR /src

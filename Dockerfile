# Initialize from docker image with Python, libraries and Nansat
FROM nansencenter/nansat:latest
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    bs4 \
    coverage \
    django==3.0 \
    django-forms-bootstrap==3.1.0 \
    django-leaflet==0.26.0 \
    psycopg2==2.8.4 \
    thredds_crawler==1.5.4 \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
COPY MANIFEST.in /tmp/
WORKDIR /tmp
RUN python setup.py install \
&&  rm -r geospaas setup.py MANIFEST.in

WORKDIR /src

# Initialize from docker image with Python, libraries and Nansat
FROM nansencenter/nansat:latest
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    coverage \
    django==2.2 \
    django-forms-bootstrap \
    django-leaflet \
    thredds_crawler \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
WORKDIR /tmp
RUN python setup.py install \
&&  rm -r geospaas setup.py

WORKDIR /src

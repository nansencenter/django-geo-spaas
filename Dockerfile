# Initialize from docker image with Python, libraries and Nansat
FROM akorosov/nansat:latest
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    coveralls \
    django \
    django-forms-bootstrap \
    django-leaflet \
    thredds_crawler \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
WORKDIR /tmp
RUN python setup.py install

WORKDIR /src

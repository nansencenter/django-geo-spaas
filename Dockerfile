# Initialize from docker image with Python, libraries and Nansat
FROM nansencenter/nansat:latest
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    coverage \
    django \
    django-forms-bootstrap \
    django-leaflet \
    psycopg2 \
    thredds_crawler \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# moving to django 3
RUN pip install --upgrade django-cors-headers

# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
COPY MANIFEST.in /tmp/
WORKDIR /tmp
RUN python setup.py install \
&&  rm -r geospaas setup.py MANIFEST.in



WORKDIR /src

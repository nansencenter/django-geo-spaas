# Initialize from docker image with Python, libraries and Nansat
FROM nansencenter/nansat:latest
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    coverage \
    django==3.0 \
    django-forms-bootstrap \
    django-leaflet \
    psycopg2 \
    thredds_crawler \
    --upgrade django-cors-headers \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# moving to django 3
#RUN pip install --upgrade django-cors-headers

# install Geo-SPaaS
COPY geospaas /tmp/geospaas
COPY setup.py /tmp/
COPY MANIFEST.in /tmp/
WORKDIR /tmp
RUN python setup.py install \
&&  rm -r geospaas setup.py MANIFEST.in



WORKDIR /src

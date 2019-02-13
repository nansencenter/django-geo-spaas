# Initialize from docker image with Python, libraries and Nansat
FROM akorosov/nansat:latest
LABEL purpose="Running and developing Django-Geo-SpaaS"
ENV PYTHONUNBUFFERED=1

# Install Django
RUN pip install \
    django \
    django-forms-bootstrap \
    django-leaflet \
&&  echo "alias ll='ls -lh'" >> /root/.bashrc

# install Geo-SPaaS into /opt/django-geo-spaas
COPY geospaas /opt/geospaas
RUN ln -s /opt/geospaas /opt/conda/lib/python3.7/site-packages/geospaas
WORKDIR /src
